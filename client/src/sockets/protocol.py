from json import dumps, loads
from struct import pack, unpack
from uuid import uuid4

from sockets.messages import KIND_REQUEST

HEADER_SIZE = 4
HEADER_FORMAT = "!I"
ENCODING = "utf-8"

def request(request_type: str, data: dict | None = None) -> dict:
    return {
        "kind": KIND_REQUEST,
        "request_id": str(uuid4()),
        "type": request_type,
        "data": data or {},
    }

def send_request(sock, request: dict) -> None:
    payload = dumps(request).encode(ENCODING)
    header = pack(HEADER_FORMAT, len(payload))
    sock.sendall(header + payload)

def recv_response(sock) -> dict | None:
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
