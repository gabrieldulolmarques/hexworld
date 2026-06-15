import json
from uuid import uuid4

from database.connection import get_connection

class PathRepository:
    def add_path_segments(
        self,
        map_id: str,
        segments: list[tuple[tuple[int, int], tuple[int, int]]],
        color: str,
        author_id: str,
    ) -> list[dict]:
        result: list[dict] = []
        with get_connection() as connection:
            for start, end in segments:
                a, b = sorted((start, end))
                waypoints_json = json.dumps(
                    [[a[0], a[1]], [b[0], b[1]]], separators=(",", ":")
                )
                existing = connection.execute(
                    """
                    SELECT id FROM path
                    WHERE map_id = ? AND color = ? AND waypoints = ?
                    """,
                    (map_id, color, waypoints_json),
                ).fetchone()
                if existing is not None:
                    path_id = existing["id"]
                else:
                    path_id = str(uuid4())
                    connection.execute(
                        "INSERT INTO path (id, map_id, waypoints, color, author_id) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (path_id, map_id, waypoints_json, color, author_id),
                    )
                result.append(
                    {
                        "path_id": path_id,
                        "waypoints": [[start[0], start[1]], [end[0], end[1]]],
                        "color": color,
                    }
                )
            connection.commit()
        return result

    def list_paths_for_map(self, map_id: str):
        with get_connection() as connection:
            return connection.execute(
                """
                SELECT id, waypoints, color, author_id, created_at, updated_at
                FROM path WHERE map_id = ?
                """,
                (map_id,),
            ).fetchall()

    def list_paths_at_tile(self, map_id: str, q: int, r: int) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, waypoints, color, author_id, created_at, updated_at
                FROM path
                WHERE map_id = ?
                  AND (
                        (json_extract(waypoints, '$[0][0]') = ?
                         AND json_extract(waypoints, '$[0][1]') = ?)
                     OR (json_extract(waypoints, '$[1][0]') = ?
                         AND json_extract(waypoints, '$[1][1]') = ?)
                  )
                """,
                (map_id, q, r, q, r),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_path_by_id(self, path_id: str):
        with get_connection() as connection:
            return connection.execute(
                "SELECT id, map_id, waypoints, color, author_id FROM path WHERE id = ?",
                (path_id,),
            ).fetchone()

    def delete_path(self, path_id: str) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM path WHERE id = ?", (path_id,))
            connection.commit()
