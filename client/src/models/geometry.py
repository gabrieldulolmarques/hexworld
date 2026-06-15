from __future__ import annotations

import math

_SQRT3 = math.sqrt(3)

Coord = tuple[int, int]
PixelPoint = tuple[float, float]

_AXIAL_DIRECTIONS: list[Coord] = [
    (1, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (0, -1),
    (1, -1),
]

def hex_to_pixel(q: float, r: float, size: float) -> tuple[float, float]:
    x = size * 1.5 * q
    y = size * _SQRT3 * (r + q / 2)
    return (x, y)

def pixel_to_hex(x: float, y: float, size: float) -> Coord:
    q = x * 2 / 3 / size
    r = (-x / 3 + _SQRT3 / 3 * y) / size
    return _round_hex(q, r)

def hex_vertices(cx: float, cy: float, size: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(6):
        a = (math.pi / 3) * i
        pts.append((cx + size * math.cos(a), cy + size * math.sin(a)))
    return pts

def hex_neighbors(q: int, r: int) -> list[Coord]:
    return [(q + dq, r + dr) for dq, dr in _AXIAL_DIRECTIONS]

def _round_hex(q: float, r: float) -> Coord:
    s = -q - r
    rq, rr, rs = round(q), round(r), round(s)
    dq, dr, ds = abs(rq - q), abs(rr - r), abs(rs - s)
    if dq > dr and dq > ds:
        rq = -rr - rs
    elif dr > ds:
        rr = -rq - rs
    return (rq, rr)

def axial_step_direction(q0: int, r0: int, q1: int, r1: int) -> int | None:
    dq, dr = q1 - q0, r1 - r0
    for i, (ddq, ddr) in enumerate(_AXIAL_DIRECTIONS):
        if dq == ddq and dr == ddr:
            return i
    return None

def _segment_key(start: Coord, end: Coord) -> tuple[Coord, Coord]:
    return (start, end) if start <= end else (end, start)

def _normalize_waypoints(waypoints: list) -> list[Coord]:
    out: list[Coord] = []
    for waypoint in waypoints:
        out.append((int(waypoint[0]), int(waypoint[1])))
    return out

def distance_point_to_segment(
    px: float,
    py: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
) -> float:
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx = ax + t * dx
    cy = ay + t * dy
    return math.hypot(px - cx, py - cy)

def distance_to_polyline(
    px: float, py: float, points: list[PixelPoint]
) -> float | None:
    if len(points) < 2:
        return None
    return min(
        distance_point_to_segment(px, py, ax, ay, bx, by)
        for (ax, ay), (bx, by) in zip(points, points[1:])
    )

def is_valid_polyline(waypoints: list) -> bool:
    wps = _normalize_waypoints(waypoints)
    if len(wps) < 2:
        return False
    seen_segments: set[tuple[Coord, Coord]] = set()
    for i in range(1, len(wps)):
        if (
            axial_step_direction(
                wps[i - 1][0],
                wps[i - 1][1],
                wps[i][0],
                wps[i][1],
            )
            is None
        ):
            return False
        key = _segment_key(wps[i - 1], wps[i])
        if key in seen_segments:
            return False
        seen_segments.add(key)
    return True
