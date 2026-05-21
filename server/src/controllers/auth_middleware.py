from collections.abc import Callable
from functools import wraps

from repositories.user_map_repository import get_role
from services.auth_service import validate_session
from transport.protocol import error_response

Handler = Callable[[dict, object, dict], dict]

_ROLE_RANK: dict[str | None, int] = {"owner": 2, "editor": 1, "viewer": 0, None: -1}
_ROLE_ERRORS: dict[str, str] = {"editor": "not_editor", "owner": "not_owner"}

def require_role(min_role: str) -> Callable:
    def decorator(handler: Handler) -> Callable[[dict, object, dict], dict]:
        @wraps(handler)
        def wrapper(request: dict, connection, auth: dict) -> dict:
            map_id = (request.get("data") or {}).get("map_id")
            if not map_id:
                return error_response(request, "missing_fields")
            role = get_role(auth["user_id"], map_id)
            if _ROLE_RANK.get(role, -1) < _ROLE_RANK[min_role]:
                error_code = _ROLE_ERRORS.get(min_role, "not_owner")
                return error_response(request, error_code)
            return handler(request, connection, auth)
        return wrapper
    return decorator

def authenticated(handler: Handler) -> Callable[[dict, object], dict]:
    @wraps(handler)
    def wrapper(request: dict, connection) -> dict:
        token = _extract_token(request)
        if not token:
            return error_response(request, "missing_fields")
        session_data, error_code = validate_session(token)
        if error_code is not None:
            return error_response(request, error_code)
        auth = {**session_data, "token": token}
        return handler(request, connection, auth)

    return wrapper

def _extract_token(request: dict) -> str:
    token = request.get("token")
    if token:
        return str(token).strip()
    data = request.get("data")
    if isinstance(data, dict):
        token = data.get("token")
        if token:
            return str(token).strip()
    return ""
