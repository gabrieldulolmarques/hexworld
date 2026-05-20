from controllers.auth_middleware import authenticated
from services.auth_service import login, logout, register
from transport.protocol import error_response, success_response

def handle_register(request: dict, conn) -> dict:
    data = request.get("data", {})

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return error_response(request, "missing_fields")

    error_code = register(username, password)

    if error_code is not None:
        return error_response(request, error_code)

    return success_response(request)

def handle_login(request: dict, conn) -> dict:
    data = request.get("data", {})

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    remember_me = bool(data.get("remember_me", False))

    if not username or not password:
        return error_response(request, "missing_fields")

    response_data, error_code = login(username, password, remember_me)

    if error_code is not None:
        return error_response(request, error_code)

    return success_response(request, response_data)

@authenticated
def handle_logout(request: dict, conn, auth: dict) -> dict:
    error_code = logout(auth["token"])

    if error_code is not None:
        return error_response(request, error_code)

    return success_response(request)

@authenticated
def handle_validate_session(request: dict, conn, auth: dict) -> dict:
    return success_response(
        request,
        {
            "user_id": auth["user_id"],
            "username": auth["username"],
        },
    )
