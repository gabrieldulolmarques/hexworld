import logging
import os
import time

import Pyro5.api

from services.auth_service import AuthService as DomainAuthService
from transport.broadcaster import Broadcaster
from transport.presence import Presence
from transport.rmi.client_session import BroadcastPresenceFn
from transport.rmi.remote_api import RequestHandlerFn, create_remote_objects
from transport.rmi.session_registry import RmiSessionRegistry

logger = logging.getLogger(__name__)

NS_LOOKUP_RETRIES = 10
NS_LOOKUP_DELAY_S = 0.5

def start_rmi_server(
    handle_request: RequestHandlerFn,
    broadcast_presence: BroadcastPresenceFn,
    *,
    broadcaster: Broadcaster,
    presence: Presence,
    domain_auth: DomainAuthService,
) -> None:
    ns_host = os.getenv("PYRO_NS_HOST", "127.0.0.1")
    ns_port = int(os.getenv("PYRO_NS_PORT", "9090"))
    bind_host = os.getenv("PYRO_HOST", "127.0.0.1")
    nat_host = os.getenv("PYRO_NAT_HOST") or None
    nat_port = os.getenv("PYRO_NAT_PORT")

    registry = RmiSessionRegistry(broadcaster, presence, broadcast_presence)
    objects = create_remote_objects(handle_request, registry, domain_auth)

    daemon_kwargs: dict = {"host": bind_host}
    if nat_host:
        daemon_kwargs["nathost"] = nat_host
        if nat_port:
            daemon_kwargs["natport"] = int(nat_port)
    daemon = Pyro5.api.Daemon(**daemon_kwargs)
    nameserver = _locate_nameserver(ns_host, ns_port)
    for name, remote_object in objects.items():
        uri = daemon.register(remote_object)
        nameserver.register(name, uri)
        logger.info("Registered PYRONAME:%s -> %s", name, uri)

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
