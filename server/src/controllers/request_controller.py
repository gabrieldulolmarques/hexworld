from traceback import format_exc

from transport.protocol import error_response

from controllers.auth_controller import (
    handle_login,
    handle_logout,
    handle_register,
    handle_validate_session,
)

REQUEST_HANDLERS = {
    "register": handle_register,
    "login": handle_login,
    "validate_session": handle_validate_session,
    "logout": handle_logout,
}

def handle_request(request: dict, connection) -> dict:
    request_type = request.get("type") or "unknown"
    handler = REQUEST_HANDLERS.get(request_type)
    if handler is None:
        return error_response(request, "unknown_type")
    try:
        return handler(request, connection)
    except Exception as exception:
        print(f"Error handling request {request}: {exception}")
        print(format_exc())
        return error_response(request, "unexpected_error")
