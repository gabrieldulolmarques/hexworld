from services import auth_service

def handle_register(request: dict) -> dict:
    username = str(request.get("username", "")).strip()
    password = str(request.get("password", ""))
    if not username or not password:
        return {"type": "register", "status": "error", "code": "missing_fields"}
    return auth_service.register(username, password)

def handle_login(request: dict) -> dict:
    username = str(request.get("username", "")).strip()
    password = str(request.get("password", ""))
    if not username or not password:
        return {"type": "login", "status": "error", "code": "missing_fields"}
    return auth_service.login(username, password)

def handle_logout(request: dict) -> dict:
    token = str(request.get("token", ""))
    if not token:
        return {"type": "logout", "status": "error", "code": "missing_fields"}
    return auth_service.logout(token)

def handle_validate_session(request: dict) -> dict:
    token = str(request.get("token", ""))
    if not token:
        return {"type": "validate_session", "status": "error", "code": "missing_fields"}
    return auth_service.validate_session(token)
