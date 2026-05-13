from json import dumps, loads
from struct import pack, unpack

HEADER_SIZE = 4
HEADER_FORMAT = "!I"
ENCODING = "utf-8"

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
    return loads(payload.decode(ENCODING))

def _recv_exact(sock, size: int) -> bytes | None:
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data
