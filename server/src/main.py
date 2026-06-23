import logging

import app as _app
from database.connection import get_connection, get_database_path
from database.schema import create_schema
from database.seed import seed_users
from transport.sockets.server import Server

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
    server = Server(
        _app.request_controller.handle_request,
        _app.publisher.presence_changed,
        broadcaster=_app.broadcaster,
        presence=_app.presence,
    )
    server.start()

def main() -> None:
    initialize_database()
    start_server()

if __name__ == "__main__":
    main()
