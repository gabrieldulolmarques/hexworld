_ROLE_RANK: dict[str | None, int] = {"owner": 2, "editor": 1, "viewer": 0, None: -1}

def has_role(role: str | None, min_role: str) -> bool:
    return _ROLE_RANK.get(role, -1) >= _ROLE_RANK[min_role]
