from database.connection import close_connection, get_connection, get_database_path
from database.schema import create_schema
from database.seed import seed_users
from transport.server import Server

def initialize_database() -> None:
    connection = get_connection()
    create_schema(connection)
    seed_users(connection)
    close_connection()
    print(f"Database ready at {get_database_path()}")

def start_server() -> None:
    server = Server()
    server.start()

def main() -> None:
    initialize_database()
    start_server()

if __name__ == "__main__":
    main()