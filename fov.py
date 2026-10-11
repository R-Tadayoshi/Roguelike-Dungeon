"""Field of view via recursive shadowcasting (eight octants)."""

from __future__ import annotations

from map_gen import GameMap

FOV_RADIUS = 8

# Transforms that map an octant's (row, col) onto map (dx, dy).
_OCTANTS = [
    (1, 0, 0, 1), (0, 1, 1, 0), (0, -1, 1, 0), (-1, 0, 0, 1),
    (-1, 0, 0, -1), (0, -1, -1, 0), (0, 1, -1, 0), (1, 0, 0, -1),
]


def compute_fov(game_map: GameMap, ox: int, oy: int, radius: int = FOV_RADIUS) -> None:
    """Refresh game_map.visible from (ox, oy) and mark newly seen tiles as explored."""
    for row in game_map.visible:
        for x in range(len(row)):
            row[x] = False
    _light(game_map, ox, oy)
    for xx, xy, yx, yy in _OCTANTS:
        _cast(game_map, ox, oy, 1, 1.0, 0.0, radius, xx, xy, yx, yy)


def _light(game_map: GameMap, x: int, y: int) -> None:
    if game_map.in_bounds(x, y):
        game_map.visible[y][x] = True
        game_map.explored[y][x] = True


def _cast(gm: GameMap, ox, oy, row, start, end, radius, xx, xy, yx, yy) -> None:
    if start < end:
        return
    radius_sq = radius * radius
    for j in range(row, radius + 1):
        dx, dy = -j - 1, -j
        blocked = False
        new_start = start
        while dx <= 0:
            dx += 1
            x = ox + dx * xx + dy * xy
            y = oy + dx * yx + dy * yy
            l_slope = (dx - 0.5) / (dy + 0.5)
            r_slope = (dx + 0.5) / (dy - 0.5)
            if start < r_slope:
                continue
            if end > l_slope:
                break
            if dx * dx + dy * dy <= radius_sq:
                _light(gm, x, y)
            if blocked:
                if not gm.is_transparent(x, y):
                    new_start = r_slope
                else:
                    blocked = False
                    start = new_start
            elif not gm.is_transparent(x, y) and j < radius:
                blocked = True
                _cast(gm, ox, oy, j + 1, start, l_slope, radius, xx, xy, yx, yy)
                new_start = r_slope
        if blocked:
            break
