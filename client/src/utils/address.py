def parse_address(raw: str) -> tuple[str, int]:
    host, _, port = raw.rpartition(":")
    if not host or not port:
        raise ValueError(f"Invalid address '{raw}', expected 'host:port'")
    return host, int(port)
