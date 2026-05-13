from transport.protocol import error_response

from controllers.auth_controller import (
    handle_register,
    handle_login,
    handle_logout,
    handle_validate_session,
)

REQUEST_HANDLERS = {
    "register": handle_register,
    "login": handle_login,
    "validate_session": handle_validate_session,
    "logout": handle_logout,
}

def handle_request(request: dict) -> dict:
    request_type = request.get("type") or "unknown"
    handler = REQUEST_HANDLERS.get(request_type)
    if handler is None:
        return error_response(request_type, "unknown_type")
    return handler(request)