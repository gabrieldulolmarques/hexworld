from services.auth_service import register, login, logout, validate_session
from transport.protocol import error_response, success_response


def handle_register(request: dict) -> dict:
    data = request.get("data", {})

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    confirm = str(data.get("confirm", ""))

    if not username or not password or not confirm:
        return error_response("register", "missing_fields")

    error_code = register(username, password, confirm)

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


def handle_logout(request: dict) -> dict:
    data = request.get("data", {})

    token = str(data.get("token", ""))

    if not token:
        return error_response("logout", "missing_fields")

    error_code = logout(token)

    if error_code is not None:
        return error_response("logout", error_code)

    return success_response("logout")


def handle_validate_session(request: dict) -> dict:
    data = request.get("data", {})

    token = str(data.get("token", ""))

    if not token:
        return error_response("validate_session", "missing_fields")

    response_data, error_code = validate_session(token)

    if error_code is not None:
        return error_response("validate_session", error_code)

    return success_response("validate_session", response_data)
