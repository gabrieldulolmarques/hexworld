import logging
import os
import threading
import time
from queue import Empty, Queue

import Pyro5.api
import Pyro5.errors
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from rmi.errors import HexworldError, register_error_serialization
from rmi.listener import MapListener
from models.server_config import parse_ns_address

logger = logging.getLogger(__name__)

_STOP = object()
_RECONNECT = object()
RECONNECT_DELAY_S = 2.0

_COMM_ERRORS = (
    Pyro5.errors.ConnectionClosedError,
    Pyro5.errors.TimeoutError,
    Pyro5.errors.CommunicationError,
    Pyro5.errors.NamingError,
)

class _Disconnected(Exception):
    """Raised inside a thunk when the required proxy is not available."""

class RemoteCall(QObject):
    """A pending remote call. Exactly one of the signals fires, on the UI thread."""

    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

class RemoteWorker(QThread):
    """Owns the Pyro proxies and runs every remote call on its own thread,
    delivering results to the UI thread via RemoteCall signals. Server-pushed
    events arrive on a MapListener and are re-emitted as evt_* signals."""

    connected = pyqtSignal()
    disconnected = pyqtSignal()

    evt_tile_changed = pyqtSignal(str, int, int, dict)
    evt_path_added = pyqtSignal(str, dict)
    evt_path_removed = pyqtSignal(str, str)
    evt_edge_changed = pyqtSignal(str, list)
    evt_presence_changed = pyqtSignal(str, list)
    evt_member_changed = pyqtSignal(str, int)
    evt_ownership_transferred = pyqtSignal(str, str)

    def __init__(self, ns_address: str | None = None) -> None:
        super().__init__()
        register_error_serialization()
        self._client_id = os.getenv("CLIENT_ID")
        self._ns_host, self._ns_port = _resolve_ns_address(ns_address)
        self._queue: Queue = Queue()
        self._running = True
        self._listener_uri: str | None = None
        self._token: str | None = None
        self._auth: Pyro5.api.Proxy | None = None
        self._session: Pyro5.api.Proxy | None = None
        self._map_session: Pyro5.api.Proxy | None = None

    # ---- public typed API (called from the UI thread) ----

    def register(self, username: str, password: str) -> RemoteCall:
        return self._submit(lambda: _none(self._auth_or_raise().register(username, password)))

    def login(self, username: str, password: str, remember_me: bool) -> RemoteCall:
        return self._submit(lambda: self._do_login(username, password, remember_me))

    def resume(self, token: str) -> RemoteCall:
        return self._submit(lambda: self._do_resume(token))

    def logout(self) -> RemoteCall:
        return self._submit(self._do_logout)

    def get_maps(self) -> RemoteCall:
        return self._submit(lambda: self._session_or_raise().get_maps())

    def create_map(self, name: str) -> RemoteCall:
        return self._submit(lambda: self._session_or_raise().create_map(name))

    def join_map(self, code: str) -> RemoteCall:
        return self._submit(lambda: self._session_or_raise().join_map(code))

    def dissociate_map(self, map_id: str) -> RemoteCall:
        return self._submit(lambda: self._session_or_raise().dissociate_map(map_id))

    def delete_map(self, map_id: str) -> RemoteCall:
        return self._submit(lambda: self._session_or_raise().delete_map(map_id))

    def open_map(self, map_id: str) -> RemoteCall:
        return self._submit(lambda: self._do_open_map(map_id))

    def close_map(self) -> RemoteCall:
        return self._submit(self._do_close_map)

    def get_tile_details(self, tile_id: str) -> RemoteCall:
        return self._submit(lambda: self._map_session_or_raise().get_tile_details(tile_id))

    def set_terrain(self, q: int, r: int, terrain_type: str) -> RemoteCall:
        return self._submit(lambda: self._map_session_or_raise().set_terrain(q, r, terrain_type))

    def set_description(self, q: int, r: int, text: str) -> RemoteCall:
        return self._submit(lambda: self._map_session_or_raise().set_description(q, r, text))

    def remove_terrain(self, tile_id: str) -> RemoteCall:
        return self._submit(lambda: self._map_session_or_raise().remove_terrain(tile_id))

    def remove_description(self, tile_id: str) -> RemoteCall:
        return self._submit(lambda: self._map_session_or_raise().remove_description(tile_id))

    def add_path(self, waypoints: list, color: str) -> RemoteCall:
        return self._submit(lambda: self._map_session_or_raise().add_path(waypoints, color))

    def remove_path(self, path_id: str) -> RemoteCall:
        return self._submit(lambda: self._map_session_or_raise().remove_path(path_id))

    def set_edge(self, q: int, r: int, edge_index: int, color: str) -> RemoteCall:
        return self._submit(lambda: self._map_session_or_raise().set_edge(q, r, edge_index, color))

    def remove_edge(self, q: int, r: int, edge_index: int) -> RemoteCall:
        return self._submit(lambda: self._map_session_or_raise().remove_edge(q, r, edge_index))

    def stop(self) -> None:
        self._running = False
        self._disconnect_best_effort()
        self._queue.put(_STOP)
        self.wait(3000)

    def set_server_address(self, raw: str) -> bool:
        try:
            host, port = parse_ns_address(raw)
        except ValueError:
            return False
        if host == self._ns_host and port == self._ns_port:
            return False
        self._ns_host = host
        self._ns_port = port
        self._reset_proxies()
        self._queue.put(_RECONNECT)
        return True

    # ---- thunks (run on the worker thread) ----

    def _do_login(self, username: str, password: str, remember_me: bool) -> dict:
        session = self._auth_or_raise().login(username, password, remember_me)
        return self._bind_session(session)

    def _do_resume(self, token: str) -> dict:
        session = self._auth_or_raise().resume(token)
        return self._bind_session(session)

    def _bind_session(self, session) -> dict:
        session._pyroClaimOwnership()
        self._session = session
        session.register_listener(self._listener_uri)
        identity = session.identity()
        self._token = identity.get("token")
        return identity

    def _do_logout(self) -> dict:
        session = self._session
        self._session = None
        self._map_session = None
        self._token = None
        if session is not None:
            session.logout()
        return {}

    def _do_open_map(self, map_id: str) -> dict:
        map_session = self._session_or_raise().open_map(map_id)
        map_session._pyroClaimOwnership()
        self._map_session = map_session
        return map_session.get_state()

    def _do_close_map(self) -> dict:
        map_session = self._map_session
        self._map_session = None
        if map_session is not None:
            map_session.close()
        return {}

    def _auth_or_raise(self):
        if self._auth is None:
            raise _Disconnected()
        return self._auth

    def _session_or_raise(self):
        if self._session is None:
            raise _Disconnected()
        return self._session

    def _map_session_or_raise(self):
        if self._map_session is None:
            raise _Disconnected()
        return self._map_session

    # ---- worker thread loop ----

    def run(self) -> None:
        self._listener_uri = self._start_callback_daemon()
        was_connected = False
        while self._running:
            try:
                self._connect()
            except Exception as exception:
                logger.warning("RMI: could not reach Name Server: %s", exception)
                if was_connected:
                    was_connected = False
                    self._reset_proxies()
                    self.disconnected.emit()
                self._sleep_reconnect()
                continue

            if not was_connected:
                was_connected = True
                self._log_connected()
                self.connected.emit()

            if self._serve():
                break

            self._reset_proxies()
            if was_connected:
                was_connected = False
                self._log_disconnected()
                self.disconnected.emit()
            if not self._running:
                break
            self._sleep_reconnect()

    def _serve(self) -> bool:
        """Process queued calls. Returns True to stop, False to reconnect."""
        while self._running:
            try:
                item = self._queue.get(timeout=0.1)
            except Empty:
                continue
            if item is _STOP:
                self._running = False
                return True
            if item is _RECONNECT:
                return False
            thunk, call = item
            try:
                result = thunk()
            except HexworldError as exception:
                call.failed.emit(exception.code)
                continue
            except _COMM_ERRORS as exception:
                logger.warning("RMI call dropped the connection: %s", exception)
                call.failed.emit("connection_lost")
                return False
            except _Disconnected:
                call.failed.emit("connection_lost")
                continue
            except Exception:
                logger.exception("Unexpected error in RMI call")
                call.failed.emit("unexpected_error")
                continue
            call.succeeded.emit(result)
        return True

    def _connect(self) -> None:
        nameserver = Pyro5.api.locate_ns(host=self._ns_host, port=self._ns_port)
        self._auth = Pyro5.api.Proxy(nameserver.lookup("hexworld.auth"))
        self._auth._pyroBind()

    def _reset_proxies(self) -> None:
        for proxy in (self._map_session, self._session, self._auth):
            if proxy is not None:
                try:
                    proxy._pyroRelease()
                except Exception:
                    pass
        self._auth = None
        self._session = None
        self._map_session = None

    def _start_callback_daemon(self) -> str:
        listener = MapListener(self)
        host = os.getenv("PYRO_CALLBACK_HOST", "0.0.0.0")
        nat_host = os.getenv("PYRO_CALLBACK_NAT_HOST") or None
        nat_port = os.getenv("PYRO_CALLBACK_NAT_PORT")
        daemon_kwargs: dict = {"host": host}
        if nat_host:
            daemon_kwargs["nathost"] = nat_host
            if nat_port:
                daemon_kwargs["natport"] = int(nat_port)
        daemon = Pyro5.api.Daemon(**daemon_kwargs)
        uri = daemon.register(listener)
        thread = threading.Thread(target=daemon.requestLoop, daemon=True)
        thread.start()
        logger.debug("RMI callback daemon started at %s", uri)
        if nat_host is None and self._ns_host not in ("127.0.0.1", "localhost"):
            logger.warning(
                "PYRO_CALLBACK_NAT_HOST is unset; server at %s may not reach "
                "this callback URI for broadcasts",
                self._ns_host,
            )
        return str(uri)

    def _disconnect_best_effort(self) -> None:
        token = self._token
        if not token:
            return
        try:
            nameserver = Pyro5.api.locate_ns(host=self._ns_host, port=self._ns_port)
            auth = Pyro5.api.Proxy(nameserver.lookup("hexworld.auth"))
            auth.disconnect(token)
            auth._pyroRelease()
        except Exception as exception:
            logger.debug("RMI: best-effort disconnect failed: %s", exception)

    def _sleep_reconnect(self) -> None:
        deadline = time.monotonic() + RECONNECT_DELAY_S
        while self._running and time.monotonic() < deadline:
            time.sleep(0.1)

    def _log_connected(self) -> None:
        logger.info(
            "Client %s connected to %s:%s (RMI)",
            self._client_id, self._ns_host, self._ns_port,
        )

    def _log_disconnected(self) -> None:
        logger.info(
            "Client %s disconnected from %s:%s (RMI)",
            self._client_id, self._ns_host, self._ns_port,
        )

    def _submit(self, thunk) -> RemoteCall:
        call = RemoteCall()
        self._queue.put((thunk, call))
        return call

def _none(_result) -> dict:
    return {}

def _resolve_ns_address(override: str | None) -> tuple[str, int]:
    if override:
        return parse_ns_address(override)
    host = os.getenv("PYRO_NS_HOST", "127.0.0.1")
    return host, int(os.getenv("PYRO_NS_PORT", "9090"))
