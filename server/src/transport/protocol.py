from json import dumps, loads
from struct import pack, unpack

HEADER_SIZE = 4
HEADER_FORMAT = "!I"
ENCODING = "utf-8"

def success_response(response_type: str, data: dict | None = None) -> dict:
    response = {
        "type": response_type,
        "status": "success",
    }
    if data is not None:
        response["data"] = data
    return response

def error_response(response_type: str, code: str) -> dict:
    return {
        "type": response_type,
        "status": "error",
        "code": code,
    }

def send_response(sock, response: dict) -> None:
    payload = dumps(response).encode(ENCODING)
    header = pack(HEADER_FORMAT, len(payload))
    sock.sendall(header + payload)

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
