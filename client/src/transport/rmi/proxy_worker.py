import logging
import os
import threading
import time
from queue import Empty, Queue

import Pyro5.api
from PyQt6.QtCore import QThread, pyqtSignal

from transport.rmi.event_callback import EventCallback

logger = logging.getLogger(__name__)

_STOP = object()
RECONNECT_DELAY_S = 2.0


class ProxyWorker(QThread):
    """Drop-in replacement for transport.sockets.Worker using Pyro5 RMI.

    Same four signals and submit/stop/reset API as the socket Worker so no
    controller needs to change when HEXWORLD_TRANSPORT=rmi is set.
    """

    connected = pyqtSignal()
    disconnected = pyqtSignal()
    response = pyqtSignal(dict)
    event = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._ns_host = os.getenv("PYRO_NS_HOST", "127.0.0.1")
        self._ns_port = int(os.getenv("PYRO_NS_PORT", "9090"))
        self._outgoing: Queue = Queue()
        self._event_queue: Queue = Queue()
        self._running = True
        self._alive = True
        self._callback_uri: str | None = None
        self._auth: Pyro5.api.Proxy | None = None
        self._catalog: Pyro5.api.Proxy | None = None
        self._view: Pyro5.api.Proxy | None = None
        self._editor: Pyro5.api.Proxy | None = None

    def submit(self, request: dict) -> bool:
        if not self._alive:
            return False
        self._outgoing.put(request)
        return True

    def reset(self) -> None:
        while not self._outgoing.empty():
            try:
                self._outgoing.get_nowait()
            except Empty:
                break
        self._running = True
        self._alive = True

    def stop(self) -> None:
        self._running = False
        self._alive = False
        self._outgoing.put(_STOP)
        self.wait(3000)

    def run(self) -> None:
        self._callback_uri = self._start_callback_daemon()
        was_connected = False
        while self._running:
            try:
                self._connect_proxies()
            except Exception as exception:
                logger.warning("RMI: could not connect to server: %s", exception)
                if was_connected:
                    was_connected = False
                    self.disconnected.emit()
                self._sleep_reconnect()
                continue

            if not was_connected:
                was_connected = True
                self.connected.emit()

            if self._serve_until_disconnect():
                break

            self._close_proxies()
            if was_connected:
                was_connected = False
                self.disconnected.emit()
            if not self._running:
                break
            self._sleep_reconnect()

    def _start_callback_daemon(self) -> str:
        callback = EventCallback(self._event_queue)
        daemon = Pyro5.api.Daemon()
        uri = daemon.register(callback)
        thread = threading.Thread(target=daemon.requestLoop, daemon=True)
        thread.start()
        logger.debug("RMI callback daemon started at %s", uri)
        return str(uri)

    def _connect_proxies(self) -> None:
        ns = Pyro5.api.locate_ns(host=self._ns_host, port=self._ns_port)
        self._auth = Pyro5.api.Proxy(ns.lookup("hexworld.auth"))
        self._catalog = Pyro5.api.Proxy(ns.lookup("hexworld.catalog"))
        self._view = Pyro5.api.Proxy(ns.lookup("hexworld.view"))
        self._editor = Pyro5.api.Proxy(ns.lookup("hexworld.editor"))
        self._auth._pyroBind()

    def _close_proxies(self) -> None:
        for proxy in (self._auth, self._catalog, self._view, self._editor):
            if proxy is not None:
                try:
                    proxy._pyroRelease()
                except Exception:
                    pass
        self._auth = self._catalog = self._view = self._editor = None

    def _serve_until_disconnect(self) -> bool:
        while self._running:
            while True:
                try:
                    payload = self._event_queue.get_nowait()
                    self.event.emit(payload)
                except Empty:
                    break

            try:
                item = self._outgoing.get(timeout=0.05)
            except Empty:
                continue

            if item is _STOP:
                self._running = False
                return True

            try:
                response = self._call_remote(item)
            except Exception as exception:
                logger.warning("RMI call failed: %s", exception)
                return False

            response["request_id"] = item.get("request_id", "")
            self._maybe_register_callback(item, response)
            self.response.emit(response)
        return True

    def _call_remote(self, request: dict) -> dict:
        request_type = request.get("type", "")
        data = request.get("data", {})
        token = data.get("token")

        match request_type:
            case "register":
                return self._auth.register(data["username"], data["password"])
            case "login":
                return self._auth.login(
                    data["username"], data["password"], data.get("remember_me", False)
                )
            case "validate_session":
                return self._auth.validate_session(token)
            case "logout":
                return self._auth.logout(token)
            case "create_map":
                return self._catalog.create_map(token, data["name"])
            case "join_map":
                return self._catalog.join_map(token, data["code"])
            case "get_maps":
                return self._catalog.get_maps(token)
            case "dissociate_map":
                return self._catalog.dissociate_map(token, data["map_id"])
            case "delete_map":
                return self._catalog.delete_map(token, data["map_id"])
            case "close_map":
                return self._catalog.close_map(token, data["map_id"])
            case "get_map_state":
                return self._view.get_map_state(token, data["map_id"])
            case "get_tile_details":
                return self._view.get_tile_details(token, data["map_id"], data["tile_id"])
            case "set_terrain":
                return self._editor.set_terrain(
                    token, data["map_id"], data["q"], data["r"], data["type"]
                )
            case "add_path":
                return self._editor.add_path(
                    token, data["map_id"], data["waypoints"], data["color"]
                )
            case "set_edge":
                return self._editor.set_edge(
                    token, data["map_id"], data["q"], data["r"],
                    data["edge_index"], data["color"],
                )
            case "remove_edge":
                return self._editor.remove_edge(
                    token, data["map_id"], data["q"], data["r"], data["edge_index"]
                )
            case "set_description":
                return self._editor.set_description(
                    token, data["map_id"], data["q"], data["r"], data["text"]
                )
            case "remove_terrain":
                return self._editor.remove_terrain(token, data["map_id"], data["tile_id"])
            case "remove_path":
                return self._editor.remove_path(token, data["map_id"], data["path_id"])
            case "remove_description":
                return self._editor.remove_description(
                    token, data["map_id"], data["tile_id"]
                )
            case _:
                raise ValueError(f"Unknown request type: {request_type!r}")

    def _maybe_register_callback(self, request: dict, response: dict) -> None:
        if response.get("status") != "success" or not self._callback_uri:
            return
        response_type = response.get("type")
        data = request.get("data", {})
        if response_type == "login":
            token = response.get("data", {}).get("token")
        elif response_type == "validate_session":
            token = data.get("token")
        else:
            return
        if token:
            try:
                self._auth.register_event_callback(token, self._callback_uri)
                logger.debug("Registered RMI event callback for token")
            except Exception as exception:
                logger.warning("Failed to register event callback: %s", exception)

    def _sleep_reconnect(self) -> None:
        deadline = time.monotonic() + RECONNECT_DELAY_S
        while self._running and time.monotonic() < deadline:
            time.sleep(0.1)
