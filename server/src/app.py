from controllers.map_event_publisher import MapEventPublisher
from repositories.description_repository import DescriptionRepository
from repositories.edge_repository import EdgeRepository
from repositories.map_repository import MapRepository
from repositories.path_repository import PathRepository
from repositories.session_repository import SessionRepository
from repositories.terrain_repository import TerrainRepository
from repositories.tile_repository import TileRepository
from repositories.user_map_repository import UserMapRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.edge_service import EdgeService
from services.map_service import MapService
from services.presence_service import PresenceService
from services.path_service import PathService
from services.tile_service import TileService
from transport.broadcaster import Broadcaster
from transport.presence import Presence

map_repository = MapRepository()
user_map_repository = UserMapRepository()
tile_repository = TileRepository()
terrain_repository = TerrainRepository()
description_repository = DescriptionRepository()
path_repository = PathRepository()
edge_repository = EdgeRepository()
user_repository = UserRepository()
session_repository = SessionRepository()

broadcaster = Broadcaster()
presence = Presence()

map_service = MapService(
    map_repository, user_map_repository, tile_repository,
    path_repository, edge_repository,
)
tile_service = TileService(
    tile_repository, terrain_repository, description_repository,
    edge_repository, path_repository, user_repository, user_map_repository,
)
path_service = PathService(path_repository, user_map_repository)
edge_service = EdgeService(edge_repository, user_map_repository)
auth_service = AuthService(user_repository, session_repository, user_map_repository)
presence_service = PresenceService(presence, user_map_repository)

publisher = MapEventPublisher(broadcaster, presence_service)
