from queue import Queue

import Pyro5.api


@Pyro5.api.expose
class EventCallback:
    """Hosted on the client; the server calls on_event to deliver broadcasts."""

    def __init__(self, event_queue: Queue) -> None:
        self._queue = event_queue

    @Pyro5.api.oneway
    def on_event(self, payload: dict) -> None:
        self._queue.put(payload)
