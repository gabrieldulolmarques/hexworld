KIND_REQUEST = "request"
KIND_RESPONSE = "response"
KIND_EVENT = "event"

STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

def success_response(request: dict, data: dict | None = None) -> dict:
    return {
        "kind": KIND_RESPONSE,
        "request_id": request.get("request_id", ""),
        "type": request.get("type", ""),
        "status": STATUS_SUCCESS,
        "data": data or {},
    }

def error_response(request: dict, code: str, data: dict | None = None) -> dict:
    return {
        "kind": KIND_RESPONSE,
        "request_id": request.get("request_id", ""),
        "type": request.get("type", ""),
        "status": STATUS_ERROR,
        "code": code,
        "data": data or {},
    }

def event(event_type: str, data: dict | None = None) -> dict:
    return {
        "kind": KIND_EVENT,
        "type": event_type,
        "data": data or {},
    }
