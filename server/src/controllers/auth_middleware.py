from collections.abc import Callable
from functools import wraps

from services.auth_service import AuthService
from transport.messages import error_response
from utils.roles import has_role

Handler = Callable[[dict, object, dict], dict]

_ROLE_ERRORS: dict[str, str] = {"editor": "not_editor", "owner": "not_owner"}

class AuthMiddleware:
    def __init__(self, auth_service: AuthService) -> None:
        self._auth_service = auth_service

    def require_role(self, min_role: str) -> Callable:
        def decorator(handler: Handler) -> Callable[[dict, object, dict], dict]:
            @wraps(handler)
            def wrapper(request: dict, connection, auth: dict) -> dict:
                map_id = (request.get("data") or {}).get("map_id")
                if not map_id:
                    return error_response(request, "missing_fields")
                role = self._auth_service.get_user_role(auth["user_id"], map_id)
                if not has_role(role, min_role):
                    error_code = _ROLE_ERRORS.get(min_role, "not_owner")
                    return error_response(request, error_code)
                return handler(request, connection, auth)

            return wrapper

        return decorator

    def authenticated(self, handler: Handler) -> Callable[[dict, object], dict]:
        @wraps(handler)
        def wrapper(request: dict, connection) -> dict:
            token = _extract_token(request)
            if not token:
                return error_response(request, "missing_fields")
            session_data, error_code = self._auth_service.validate_session(token)
            if error_code is not None:
                return error_response(request, error_code)
            auth = {**session_data, "token": token}
            connection.bind_user(auth["user_id"], auth["username"])
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
