KIND_EVENT = "event"

def event(event_type: str, data: dict | None = None) -> dict:
    return {
        "kind": KIND_EVENT,
        "type": event_type,
        "data": data or {},
    }
