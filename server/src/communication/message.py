import json
import struct

HEADER_SIZE = 4
HEADER_FORMAT = "!I"
ENCODING = "utf-8"

def send_message(sock, message: dict) -> None:
    payload = json.dumps(message).encode(ENCODING)
    header = struct.pack(HEADER_FORMAT, len(payload))
    sock.sendall(header + payload)

def recv_message(sock) -> dict | None:
    header = _recv_exact(sock, HEADER_SIZE)
    if not header:
        return None
    size = struct.unpack(HEADER_FORMAT, header)[0]
    payload = _recv_exact(sock, size)
    if not payload:
        return None
    return json.loads(payload.decode(ENCODING))

def _recv_exact(sock, size: int) -> bytes | None:
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data
