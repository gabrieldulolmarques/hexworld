from controllers.auth_middleware import authenticated
from services.auth_service import login, logout, register
from transport.protocol import error_response, success_response

def handle_register(request: dict) -> dict:
    data = request.get("data", {})

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return error_response("register", "missing_fields")

    error_code = register(username, password)

    if error_code is not None:
        return error_response("register", error_code)

    return success_response("register")

def handle_login(request: dict) -> dict:
    data = request.get("data", {})

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    remember_me = bool(data.get("remember_me", False))

    if not username or not password:
        return error_response("login", "missing_fields")

    response_data, error_code = login(username, password, remember_me)

    if error_code is not None:
        return error_response("login", error_code)

    return success_response("login", response_data)

@authenticated
def handle_logout(request: dict, auth: dict) -> dict:
    error_code = logout(auth["token"])

    if error_code is not None:
        return error_response("logout", error_code)

    return success_response("logout")

@authenticated
def handle_validate_session(request: dict, auth: dict) -> dict:
    return success_response(
        "validate_session",
        {
            "user_id": auth["user_id"],
            "username": auth["username"],
        },
    )
