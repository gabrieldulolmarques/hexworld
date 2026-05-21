"""
Hex grid geometry — flat-top axial coordinates (q, r).

Flat-top: each hexagon has a horizontal flat edge at the top and bottom,
with vertices on the left/right sides.  Follows the redblobgames convention
(https://www.redblobgames.com/grids/hexagons/).

Pixel convention (origin at canvas centre):
  x grows right, y grows down (screen coordinates).
  hex_to_pixel / pixel_to_hex are exact inverses (up to floating-point rounding).
"""
import math

_SQRT3 = math.sqrt(3)

Coord = tuple[int, int]

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
