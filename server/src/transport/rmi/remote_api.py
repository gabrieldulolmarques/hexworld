from services.auth_service import AuthService as DomainAuthService
from transport.rmi.auth_service import AuthService
from transport.rmi.base import RequestHandlerFn
from transport.rmi.map_catalog import MapCatalog
from transport.rmi.map_editor import MapEditor
from transport.rmi.map_view import MapView
from transport.rmi.session_registry import RmiSessionRegistry


def create_remote_objects(
    handle_request: RequestHandlerFn,
    registry: RmiSessionRegistry,
    domain_auth: DomainAuthService,
) -> dict[str, object]:
    return {
        "hexworld.auth": AuthService(handle_request, registry, domain_auth),
        "hexworld.catalog": MapCatalog(handle_request, registry),
        "hexworld.view": MapView(handle_request, registry),
        "hexworld.editor": MapEditor(handle_request, registry),
    }
