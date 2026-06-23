import logging
import os
import time

import Pyro5.api

from events.publisher import MapEventPublisher
from services.auth_service import AuthService as DomainAuthService
from services.edge_service import EdgeService
from services.map_service import MapService
from services.path_service import PathService
from services.tile_service import TileService
from events.broadcaster import Broadcaster
from events.presence import Presence
from rmi.auth_service import AuthService
from rmi.context import RmiContext
from rmi.errors import register_error_serialization
from rmi.registry import RmiSessionRegistry

logger = logging.getLogger(__name__)

NS_LOOKUP_RETRIES = 10
NS_LOOKUP_DELAY_S = 0.5

NAME_SERVER_OBJECT = "hexworld.auth"

def start_rmi_server(
    *,
    auth_service: DomainAuthService,
    map_service: MapService,
    tile_service: TileService,
    path_service: PathService,
    edge_service: EdgeService,
    publisher: MapEventPublisher,
    presence: Presence,
    broadcaster: Broadcaster,
) -> None:
    register_error_serialization()

    ns_host = os.getenv("PYRO_NS_HOST", "127.0.0.1")
    ns_port = int(os.getenv("PYRO_NS_PORT", "9090"))
    bind_host = os.getenv("PYRO_HOST", "127.0.0.1")
    nat_host = os.getenv("PYRO_NAT_HOST") or None
    nat_port = os.getenv("PYRO_NAT_PORT")

    daemon_kwargs: dict = {"host": bind_host}
    if nat_host:
        daemon_kwargs["nathost"] = nat_host
        if nat_port:
            daemon_kwargs["natport"] = int(nat_port)
    daemon = Pyro5.api.Daemon(**daemon_kwargs)

    context = RmiContext(
        daemon=daemon,
        auth_service=auth_service,
        map_service=map_service,
        tile_service=tile_service,
        path_service=path_service,
        edge_service=edge_service,
        publisher=publisher,
        presence=presence,
        broadcaster=broadcaster,
        registry=RmiSessionRegistry(),
    )

    gateway = AuthService(context)
    uri = daemon.register(gateway)
    nameserver = _locate_nameserver(ns_host, ns_port)
    nameserver.register(NAME_SERVER_OBJECT, uri)
    logger.info("Registered PYRONAME:%s -> %s", NAME_SERVER_OBJECT, uri)

    try:
        daemon.requestLoop()
    except KeyboardInterrupt:
        logger.info("RMI server stopped by keyboard interrupt")
    finally:
        daemon.close()

def _locate_nameserver(host: str, port: int):
    last_error: Exception | None = None
    for attempt in range(NS_LOOKUP_RETRIES):
        try:
            nameserver = Pyro5.api.locate_ns(host=host, port=port)
            logger.info("Connected to Name Server at %s:%s", host, port)
            return nameserver
        except Exception as exception:
            last_error = exception
            logger.warning(
                "Name Server not ready (attempt %s/%s): %s",
                attempt + 1,
                NS_LOOKUP_RETRIES,
                exception,
            )
            time.sleep(NS_LOOKUP_DELAY_S)
    raise RuntimeError(
        f"Could not connect to Pyro5 Name Server at {host}:{port}"
    ) from last_error
