from threading import Lock
from weakref import WeakValueDictionary

_tile_locks: WeakValueDictionary = WeakValueDictionary()
_tile_locks_lock = Lock()

def get_tile_lock(map_id: str, q: int, r: int) -> Lock:
    key = (map_id, q, r)
    with _tile_locks_lock:
        lock = _tile_locks.get(key)
        if lock is None:
            lock = Lock()
            _tile_locks[key] = lock
        return lock
