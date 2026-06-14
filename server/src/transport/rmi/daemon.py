import logging
import os
import time

import Pyro5.api

from transport.broadcaster import Broadcaster
from transport.presence import Presence
from transport.rmi.client_session import BroadcastPresenceFn
from transport.rmi.remote_api import RequestHandlerFn, create_hexworld_api

logger = logging.getLogger(__name__)

HEXWORLD_API_NAME = "hexworld.api"
NS_LOOKUP_RETRIES = 10
NS_LOOKUP_DELAY_S = 0.5

def start_rmi_server(
    handle_request: RequestHandlerFn,
    broadcast_presence: BroadcastPresenceFn,
    *,
    broadcaster: Broadcaster,
    presence: Presence,
) -> None:
    ns_host = os.getenv("PYRO_NS_HOST", "127.0.0.1")
    ns_port = int(os.getenv("PYRO_NS_PORT", "9090"))
    bind_host = os.getenv("PYRO_HOST", "0.0.0.0")

    api_class = create_hexworld_api(
        handle_request,
        broadcast_presence,
        broadcaster,
        presence,
    )

    daemon = Pyro5.api.Daemon(host=bind_host)
    uri = daemon.register(api_class)

    nameserver = _locate_nameserver(ns_host, ns_port)
    nameserver.register(HEXWORLD_API_NAME, uri)

    logger.info("RMI server registered as PYRONAME:%s", HEXWORLD_API_NAME)
    logger.info("Daemon URI: %s", uri)
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
