from json import dumps, loads
from struct import pack, unpack

HEADER_SIZE = 4
HEADER_FORMAT = "!I"
ENCODING = "utf-8"
MAX_PAYLOAD_SIZE = 32 * 1024 * 1024

def send_response(sock, response: dict) -> None:
    payload = dumps(response).encode(ENCODING)
    header = pack(HEADER_FORMAT, len(payload))
    sock.sendall(header + payload)

def recv_request(sock) -> dict | None:
    header = _recv_exact(sock, HEADER_SIZE)
    if not header:
        return None
    size = unpack(HEADER_FORMAT, header)[0]
    if size > MAX_PAYLOAD_SIZE:
        raise ValueError(f"Payload size {size} exceeds limit {MAX_PAYLOAD_SIZE}")
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
