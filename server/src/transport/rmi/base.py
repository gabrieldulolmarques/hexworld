from collections.abc import Callable
from uuid import uuid4

from transport.messages import error_response
from transport.rmi.session_registry import RmiSessionRegistry
from transport.session import ClientSession

RequestHandlerFn = Callable[[dict, ClientSession], dict]


class _RemoteBase:
    def __init__(
        self, handle_request: RequestHandlerFn, registry: RmiSessionRegistry
    ) -> None:
        self._handle_request = handle_request
        self._registry = registry

    def _auth_call(self, request_type: str, token: str, data: dict) -> dict:
        token = str(token or "").strip()
        if not token:
            request = {"type": request_type, "request_id": str(uuid4()), "data": data}
            return error_response(request, "missing_fields")
        session = self._registry.get_or_create(token)
        return self._dispatch(request_type, {"token": token, **data}, session)

    def _anon_call(self, request_type: str, data: dict) -> dict:
        session = self._registry.transient()
        try:
            return self._dispatch(request_type, data, session)
        finally:
            session.cleanup()

    def _dispatch(self, request_type: str, data: dict, session: ClientSession) -> dict:
        request = {"type": request_type, "request_id": str(uuid4()), "data": data}
        return self._handle_request(request, session)
