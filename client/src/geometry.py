"""
Hex grid geometry — flat-top axial coordinates (q, r).

Flat-top: each hexagon has a horizontal flat edge at the top and bottom,
with vertices on the left/right sides.  Follows the redblobgames convention
(https://www.redblobgames.com/grids/hexagons/).

Pixel convention (origin at canvas centre):
  x grows right, y grows down (screen coordinates).
  hex_to_pixel / pixel_to_hex are exact inverses (up to floating-point rounding).
"""
from __future__ import annotations

import math

_SQRT3 = math.sqrt(3)

Coord = tuple[int, int]
PixelPoint = tuple[float, float]

_AXIAL_DIRECTIONS: list[Coord] = [
    (1, 0), (0, 1), (-1, 1),
    (-1, 0), (0, -1), (1, -1),
]


def hex_to_pixel(q: float, r: float, size: float) -> tuple[float, float]:
    # flat-top:  x = size * 3/2 * q
    #            y = size * (sqrt(3)/2 * q + sqrt(3) * r)
    x = size * 1.5 * q
    y = size * _SQRT3 * (r + q / 2)
    return (x, y)


def pixel_to_hex(x: float, y: float, size: float) -> Coord:
    # flat-top inverse:  q = x * 2/3 / size
    #                    r = (-x/3 + sqrt(3)/3 * y) / size
    q = x * 2 / 3 / size
    r = (-x / 3 + _SQRT3 / 3 * y) / size
    return _round_hex(q, r)


def hex_vertices(cx: float, cy: float, size: float) -> list[tuple[float, float]]:
    # flat-top: vertex angles 0°, 60°, 120°, 180°, 240°, 300° (no offset)
    pts: list[tuple[float, float]] = []
    for i in range(6):
        a = (math.pi / 3) * i          # 0° offset → flat-top
        pts.append((cx + size * math.cos(a), cy + size * math.sin(a)))
    return pts


def hex_neighbors(q: int, r: int) -> list[Coord]:
    return [(q + dq, r + dr) for dq, dr in _AXIAL_DIRECTIONS]


def hex_distance(q0: int, r0: int, q1: int, r1: int) -> int:
    """Chebyshev distance in cube space — equivalent to hex step count."""
    dq, dr = q1 - q0, r1 - r0
    return max(abs(dq), abs(dr), abs(dq + dr))


def axial_line_cells(q0: int, r0: int, q1: int, r1: int) -> list[Coord]:
    """All hex cells on the straight line from (q0,r0) to (q1,r1), inclusive."""
    x0, y0, z0 = q0, -q0 - r0, r0
    x1, y1, z1 = q1, -q1 - r1, r1
    n = int(max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)))
    if n == 0:
        return [(q0, r0)]
    out: list[Coord] = []
    for i in range(n + 1):
        t = i / n
        cx, cy, cz = _cube_round(
            x0 + (x1 - x0) * t,
            y0 + (y1 - y0) * t,
            z0 + (z1 - z0) * t,
        )
        coord = (cx, cz)
        if out and coord == out[-1]:
            continue
        out.append(coord)
    return out


def _round_hex(q: float, r: float) -> Coord:
    s = -q - r
    rq, rr, rs = round(q), round(r), round(s)
    dq, dr, ds = abs(rq - q), abs(rr - r), abs(rs - s)
    if dq > dr and dq > ds:
        rq = -rr - rs
    elif dr > ds:
        rr = -rq - rs
    return (rq, rr)


def _cube_round(x: float, y: float, z: float) -> tuple[int, int, int]:
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return (int(rx), int(ry), int(rz))


def axial_step_direction(q0: int, r0: int, q1: int, r1: int) -> int | None:
    """Index in _AXIAL_DIRECTIONS for a single hex step, or None if not neighbors."""
    dq, dr = q1 - q0, r1 - r0
    for i, (ddq, ddr) in enumerate(_AXIAL_DIRECTIONS):
        if dq == ddq and dr == ddr:
            return i
    return None


def _segment_key(start: Coord, end: Coord) -> tuple[Coord, Coord]:
    return (start, end) if start <= end else (end, start)


def _normalize_waypoints(waypoints: list) -> list[Coord]:
    out: list[Coord] = []
    for wp in waypoints:
        out.append((int(wp[0]), int(wp[1])))
    return out


def _path_pixel_points_free(waypoints: list[Coord], hex_size: float) -> list[tuple[float, float]]:
    return [hex_to_pixel(q, r, hex_size) for q, r in waypoints]


def path_pixel_points(waypoints: list, hex_size: float) -> list[tuple[float, float]]:
    """Project hex waypoints to pixel offsets (relative to canvas origin)."""
    wps = _normalize_waypoints(waypoints)
    return _path_pixel_points_free(wps, hex_size)


def _quadratic_point(
    start: PixelPoint,
    control: PixelPoint,
    end: PixelPoint,
    t: float,
) -> PixelPoint:
    inv = 1.0 - t
    x = inv * inv * start[0] + 2 * inv * t * control[0] + t * t * end[0]
    y = inv * inv * start[1] + 2 * inv * t * control[1] + t * t * end[1]
    return (x, y)


def _append_quadratic_samples(
    out: list[PixelPoint],
    start: PixelPoint,
    control: PixelPoint,
    end: PixelPoint,
    samples: int,
) -> None:
    steps = max(1, samples)
    for step in range(1, steps + 1):
        out.append(_quadratic_point(start, control, end, step / steps))


def smooth_path_points(
    points: list[PixelPoint],
    curve: float = 1.0,
    *,
    samples_per_curve: int = 12,
) -> list[PixelPoint]:
    """Sample the JSX smoothPath Q/T curve as plain pixel points.

    The prototype treats ``curve`` as a threshold: values near zero render a
    straight first-to-last segment, while larger values use chained quadratic
    curves through the intermediate points.
    """
    pts = [(float(x), float(y)) for x, y in points]
    if len(pts) < 2:
        return pts
    if len(pts) == 2 or curve <= 0.05:
        return [pts[0], pts[-1]]

    out: list[PixelPoint] = [pts[0]]
    start = pts[0]
    last_control: PixelPoint | None = None
    for i in range(1, len(pts) - 1):
        control = pts[i]
        next_pt = pts[i + 1]
        end = (
            control[0] + (next_pt[0] - control[0]) * 0.5,
            control[1] + (next_pt[1] - control[1]) * 0.5,
        )
        _append_quadratic_samples(out, start, control, end, samples_per_curve)
        start = end
        last_control = control

    if last_control is not None:
        smooth_control = (
            start[0] * 2.0 - last_control[0],
            start[1] * 2.0 - last_control[1],
        )
        _append_quadratic_samples(out, start, smooth_control, pts[-1], samples_per_curve)
    return out


def smooth_path_pixel_points(
    waypoints: list,
    hex_size: float,
    curve: float = 1.0,
    *,
    samples_per_curve: int = 12,
) -> list[PixelPoint]:
    points = path_pixel_points(waypoints, hex_size)
    return smooth_path_points(points, curve, samples_per_curve=samples_per_curve)


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


def distance_to_polyline(px: float, py: float, points: list[PixelPoint]) -> float | None:
    if len(points) < 2:
        return None
    return min(
        distance_point_to_segment(px, py, ax, ay, bx, by)
        for (ax, ay), (bx, by) in zip(points, points[1:])
    )


def is_valid_polyline(waypoints: list) -> bool:
    """At least two points; each undirected neighbor segment may appear once."""
    wps = _normalize_waypoints(waypoints)
    if len(wps) < 2:
        return False
    seen_segments: set[tuple[Coord, Coord]] = set()
    for i in range(1, len(wps)):
        if axial_step_direction(
            wps[i - 1][0],
            wps[i - 1][1],
            wps[i][0],
            wps[i][1],
        ) is None:
            return False
        key = _segment_key(wps[i - 1], wps[i])
        if key in seen_segments:
            return False
        seen_segments.add(key)
    return True
