from contextlib import contextmanager
from os import getenv
from pathlib import Path
from queue import Empty, Queue
from sqlite3 import Connection, Row, connect
from threading import Lock
from traceback import format_exc

POOL_SIZE = 8

_pool: Queue[Connection] = Queue(maxsize=POOL_SIZE)
_pool_lock = Lock()
_pool_ready = False

def get_database_path() -> Path:
    configured = getenv("DATABASE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "hexworld.db"

@contextmanager
def get_connection():
    """Borrow a connection from the pool for the duration of a `with` block.

    Connections are safe to share across threads (`check_same_thread=False`) but
    each handler must hold one for its whole unit of work. Always use `with`.
    """
    _ensure_pool()
    connection = _pool.get()
    try:
        yield connection
    finally:
        _pool.put(connection)

def close_pool() -> None:
    """Drain and close every pooled connection. Call from Server.stop()."""
    global _pool_ready
    with _pool_lock:
        if not _pool_ready:
            return
        while True:
            try:
                connection = _pool.get_nowait()
            except Empty:
                break
            try:
                connection.close()
            except Exception as exception:
                print(f"Error closing pooled connection: {exception}")
                print(format_exc())
        _pool_ready = False

def _ensure_pool() -> None:
    global _pool_ready
    if _pool_ready:
        return
    with _pool_lock:
        if _pool_ready:
            return
        database_path = get_database_path()
        database_path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(POOL_SIZE):
            connection = connect(database_path, check_same_thread=False)
            connection.row_factory = Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            _pool.put(connection)
        _pool_ready = True
