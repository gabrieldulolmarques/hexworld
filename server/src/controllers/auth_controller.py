from services.auth_service import AuthService
from transport.messages import error_response, success_response
from transport.session import ClientSession

class AuthController:
    def __init__(self, auth_service: AuthService) -> None:
        self._auth_service = auth_service

    def handle_register(self, request: dict, connection: ClientSession) -> dict:
        data = request.get("data", {})
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))
        if not username or not password:
            return error_response(request, "missing_fields")
        error_code = self._auth_service.register(username, password)
        if error_code is not None:
            return error_response(request, error_code)
        return success_response(request)

    def handle_login(self, request: dict, connection: ClientSession) -> dict:
        data = request.get("data", {})
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))
        remember_me = bool(data.get("remember_me", False))
        if not username or not password:
            return error_response(request, "missing_fields")
        response_data, error_code = self._auth_service.login(
            username, password, remember_me
        )
        if error_code is not None:
            return error_response(request, error_code)
        return success_response(request, response_data)

    def handle_logout(self, request: dict, connection: ClientSession, auth: dict) -> dict:
        error_code = self._auth_service.logout(auth["token"])
        if error_code is not None:
            return error_response(request, error_code)
        return success_response(request)

    def handle_validate_session(
        self, request: dict, connection: ClientSession, auth: dict
    ) -> dict:
        return success_response(
            request,
            {
                "user_id": auth["user_id"],
                "username": auth["username"],
            },
        )
