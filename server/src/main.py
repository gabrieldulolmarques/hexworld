import logging

import app as _app
from database.connection import get_connection, get_database_path
from database.schema import create_schema
from database.seed import seed_users
from rmi.daemon import start_rmi_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)

def initialize_database() -> None:
    with get_connection() as connection:
        create_schema(connection)
        seed_users(connection)
    logger.info("Database ready at %s", get_database_path())

def start_server() -> None:
    start_rmi_server(
        auth_service=_app.auth_service,
        map_service=_app.map_service,
        tile_service=_app.tile_service,
        path_service=_app.path_service,
        edge_service=_app.edge_service,
        publisher=_app.publisher,
        presence=_app.presence,
        broadcaster=_app.broadcaster,
    )

def main() -> None:
    initialize_database()
    start_server()

if __name__ == "__main__":
    main()
