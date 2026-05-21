#!/usr/bin/env python3
"""Add users to a map until it reaches MAX_MAP_MEMBERS (128).

Usage (from repo root):
  python3 server/scripts/fill_map_members.py 679e-f6d7
  python3 server/scripts/fill_map_members.py be892f56-0c72-4866-96cf-013cb9209b59

Accepts full map UUID or editor/viewer invite code fragment.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from database.connection import get_connection, get_database_path
from services.auth_service import hash_password

MAX_MAP_MEMBERS = 128
DEFAULT_PASSWORD = "password1"


def resolve_map_id(connection, ref: str) -> tuple[str, str]:
    row = connection.execute(
        "SELECT id, name FROM map WHERE id = ?",
        (ref,),
    ).fetchone()
    if row is not None:
        return row["id"], row["name"]
    row = connection.execute(
        """
        SELECT id, name FROM map
        WHERE editor_code = ? OR viewer_code = ?
        """,
        (ref, ref),
    ).fetchone()
    if row is not None:
        return row["id"], row["name"]
    row = connection.execute(
        """
        SELECT id, name FROM map
        WHERE id LIKE ? OR editor_code LIKE ? OR viewer_code LIKE ?
        """,
        (f"%{ref}%", f"%{ref}%", f"%{ref}%"),
    ).fetchone()
    if row is not None:
        return row["id"], row["name"]
    raise SystemExit(f"Map not found for reference: {ref!r}")


def count_members(connection, map_id: str) -> int:
    row = connection.execute(
        "SELECT COUNT(*) AS n FROM user_map WHERE map_id = ?",
        (map_id,),
    ).fetchone()
    return int(row["n"])


def existing_usernames(connection) -> set[str]:
    return {
        row["username"]
        for row in connection.execute("SELECT username FROM user").fetchall()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill a map up to 128 members.")
    parser.add_argument(
        "map_ref",
        help="Map UUID, editor code, or viewer code (e.g. 679e-f6d7)",
    )
    parser.add_argument(
        "--role",
        default="viewer",
        choices=("viewer", "editor"),
        help="Role for new members (default: viewer)",
    )
    args = parser.parse_args()

    db_path = get_database_path()
    print(f"Database: {db_path}")

    with get_connection() as connection:
        map_id, map_name = resolve_map_id(connection, args.map_ref)
        current = count_members(connection, map_id)
        needed = MAX_MAP_MEMBERS - current

        if needed <= 0:
            print(f"Map {map_name!r} ({map_id}) already has {current} members (max {MAX_MAP_MEMBERS}).")
            return

        print(f"Map: {map_name!r} ({map_id})")
        print(f"Members now: {current} → adding {needed} as {args.role}")

        taken = existing_usernames(connection)
        password_hash = hash_password(DEFAULT_PASSWORD)
        added = 0
        index = 1

        while added < needed:
            username = f"mem{index:04d}"
            index += 1
            if username in taken:
                continue
            user_id = str(uuid4())
            connection.execute(
                "INSERT INTO user (id, username, password_hash) VALUES (?, ?, ?)",
                (user_id, username, password_hash),
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO user_map (user_id, map_id, role)
                VALUES (?, ?, ?)
                """,
                (user_id, map_id, args.role),
            )
            taken.add(username)
            added += 1

        connection.commit()
        final = count_members(connection, map_id)
        print(f"Done: added {added} users. Members now: {final}/{MAX_MAP_MEMBERS}")


if __name__ == "__main__":
    main()
