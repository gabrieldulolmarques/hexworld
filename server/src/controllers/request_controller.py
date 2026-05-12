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
    request_type = request.get("type")

    if request_type is None:
        return error_response("unknown", "missing_request_type")

    handler = REQUEST_HANDLERS.get(request_type)

    if handler is None:
        return error_response(request_type, "invalid_request_type")

    return handler(request)