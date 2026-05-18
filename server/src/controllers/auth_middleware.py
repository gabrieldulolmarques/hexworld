from collections.abc import Callable
from functools import wraps

from services.auth_service import validate_session
from transport.protocol import error_response

Handler = Callable[[dict, dict], dict]

def authenticated(handler: Handler) -> Callable[[dict], dict]:
    @wraps(handler)
    def wrapper(request: dict) -> dict:
        request_type = request.get("type") or "unknown"
        token = _extract_token(request)
        if not token:
            return error_response(request_type, "missing_fields")
        session_data, error_code = validate_session(token)
        if error_code is not None:
            return error_response(request_type, error_code)
        auth = {**session_data, "token": token}
        return handler(request, auth)

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
