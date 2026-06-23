from dataclasses import dataclass

import Pyro5.api

from events.publisher import MapEventPublisher
from services.auth_service import AuthService
from services.edge_service import EdgeService
from services.map_service import MapService
from services.path_service import PathService
from services.tile_service import TileService
from events.broadcaster import Broadcaster
from events.presence import Presence
from rmi.registry import RmiSessionRegistry

@dataclass
class RmiContext:
    daemon: Pyro5.api.Daemon
    auth_service: AuthService
    map_service: MapService
    tile_service: TileService
    path_service: PathService
    edge_service: EdgeService
    publisher: MapEventPublisher
    presence: Presence
    broadcaster: Broadcaster
    registry: RmiSessionRegistry
