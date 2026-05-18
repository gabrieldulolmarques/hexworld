from json import dumps, loads
from struct import pack, unpack

HEADER_SIZE = 4
HEADER_FORMAT = "!I"
ENCODING = "utf-8"

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

def send_response(sock, response: dict) -> None:
    payload = dumps(response).encode(ENCODING)
    header = pack(HEADER_FORMAT, len(payload))
    sock.sendall(header + payload)

def send_event(sock, event: dict) -> None:
    send_response(sock, event)

def recv_request(sock) -> dict | None:
    header = _recv_exact(sock, HEADER_SIZE)
    if not header:
        return None
    size = unpack(HEADER_FORMAT, header)[0]
    payload = _recv_exact(sock, size)
    if not payload:
        return None
    try:
        return loads(payload.decode(ENCODING))
    except Exception:
        return None

def _recv_exact(sock, size: int) -> bytes | None:
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data
