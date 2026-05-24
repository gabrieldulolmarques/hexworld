import json
from uuid import uuid4

from database.connection import get_connection

def get_structure(tile_id: str):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT tile_id, type, author_id, created_at, updated_at
            FROM structure WHERE tile_id = ?
            """,
            (tile_id,),
        ).fetchone()

def upsert_structure(tile_id: str, structure_type: str, author_id: str) -> None:
    """One structure per tile (RF12). ON CONFLICT keeps the primary key stable."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO structure (tile_id, type, author_id)
            VALUES (?, ?, ?)
            ON CONFLICT(tile_id) DO UPDATE SET
                type = excluded.type,
                author_id = excluded.author_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (tile_id, structure_type, author_id),
        )
        connection.commit()
    from repositories.tile_repository import touch_tile

    touch_tile(tile_id)

def add_road_segment(
    map_id: str,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str,
    author_id: str,
) -> tuple[str, bool]:
    """Persist one road segment. Returns (segment id, created?)."""
    a, b = sorted((start, end))
    waypoints_json = json.dumps([[a[0], a[1]], [b[0], b[1]]], separators=(",", ":"))
    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT id FROM road
            WHERE map_id = ? AND color = ? AND waypoints = ?
            """,
            (map_id, color, waypoints_json),
        ).fetchone()
        if existing is not None:
            return existing["id"], False
        road_id = str(uuid4())
        connection.execute(
            "INSERT INTO road (id, map_id, waypoints, color, author_id) VALUES (?, ?, ?, ?, ?)",
            (road_id, map_id, waypoints_json, color, author_id),
        )
        connection.commit()
    return road_id, True

def list_roads_for_map(map_id: str):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, waypoints, color, author_id, created_at, updated_at
            FROM road WHERE map_id = ?
            """,
            (map_id,),
        ).fetchall()


def list_roads_at_cell(map_id: str, q: int, r: int) -> list[dict]:
    """Road segments with an endpoint on (q, r)."""
    cell = (q, r)
    found: list[dict] = []
    for row in list_roads_for_map(map_id):
        row = dict(row)
        waypoints = json.loads(row["waypoints"])
        if len(waypoints) < 2:
            continue
        a = (int(waypoints[0][0]), int(waypoints[0][1]))
        b = (int(waypoints[1][0]), int(waypoints[1][1]))
        if cell == a or cell == b:
            found.append(row)
    return found


def get_road_by_id(road_id: str):
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, map_id, waypoints, color, author_id FROM road WHERE id = ?",
            (road_id,),
        ).fetchone()

def delete_road(road_id: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM road WHERE id = ?", (road_id,))
        connection.commit()


def list_inner_edges_for_map(map_id: str):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT map_id, q, r, edges, color, author_id, created_at, updated_at
            FROM hex_inner_edge
            WHERE map_id = ?
            """,
            (map_id,),
        ).fetchall()


def get_inner_edge_cell(map_id: str, q: int, r: int):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT map_id, q, r, edges, color, author_id, created_at, updated_at
            FROM hex_inner_edge
            WHERE map_id = ? AND q = ? AND r = ?
            """,
            (map_id, q, r),
        ).fetchone()


def upsert_inner_edge_cell(
    map_id: str,
    q: int,
    r: int,
    edges: int,
    color: str,
    author_id: str,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO hex_inner_edge (map_id, q, r, edges, color, author_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(map_id, q, r) DO UPDATE SET
                edges = excluded.edges,
                color = excluded.color,
                author_id = excluded.author_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (map_id, q, r, edges, color, author_id),
        )
        connection.commit()


def delete_inner_edge_cell(map_id: str, q: int, r: int) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM hex_inner_edge WHERE map_id = ? AND q = ? AND r = ?",
            (map_id, q, r),
        )
        connection.commit()


def update_inner_edge_cell(
    map_id: str,
    q: int,
    r: int,
    edges: int,
    color: str,
    author_id: str,
) -> None:
    if edges:
        upsert_inner_edge_cell(map_id, q, r, edges, color, author_id)
        return
    delete_inner_edge_cell(map_id, q, r)


def get_description(tile_id: str):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT tile_id, text, author_id, created_at, updated_at
            FROM description WHERE tile_id = ?
            """,
            (tile_id,),
        ).fetchone()

def upsert_description(tile_id: str, text: str, author_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO description (tile_id, text, author_id)
            VALUES (?, ?, ?)
            ON CONFLICT(tile_id) DO UPDATE SET
                text = excluded.text,
                author_id = excluded.author_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (tile_id, text, author_id),
        )
        connection.commit()
    from repositories.tile_repository import touch_tile

    touch_tile(tile_id)

def delete_structure(tile_id: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM structure WHERE tile_id = ?", (tile_id,))
        connection.commit()
    from repositories.tile_repository import touch_tile

    touch_tile(tile_id)

def delete_description(tile_id: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM description WHERE tile_id = ?", (tile_id,))
        connection.commit()
    from repositories.tile_repository import touch_tile

    touch_tile(tile_id)

def get_cell_details(tile_id: str, map_id: str, q: int, r: int) -> dict:
    structure = get_structure(tile_id)
    description = get_description(tile_id)
    inner_edge = get_inner_edge_cell(map_id, q, r)
    return {
        "structure": dict(structure) if structure else None,
        "description": dict(description) if description else None,
        "inner_edge": dict(inner_edge) if inner_edge else None,
    }
