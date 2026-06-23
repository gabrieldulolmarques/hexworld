from uuid import uuid4

KIND_REQUEST = "request"
KIND_RESPONSE = "response"
KIND_EVENT = "event"

STATUS_ERROR = "error"

def request(request_type: str, data: dict | None = None) -> dict:
    return {
        "kind": KIND_REQUEST,
        "request_id": str(uuid4()),
        "type": request_type,
        "data": data or {},
    }
