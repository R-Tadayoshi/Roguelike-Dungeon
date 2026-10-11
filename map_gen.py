"""Procedural dungeon floor generation: rectangular rooms joined by corridors."""

from __future__ import annotations

import random
from dataclasses import dataclass

MAP_WIDTH = 70
MAP_HEIGHT = 21

WALL = "#"
FLOOR = "."
STAIRS = ">"

ROOM_MIN_W, ROOM_MAX_W = 5, 12
ROOM_MIN_H, ROOM_MAX_H = 3, 6
MAX_ROOMS = 10
PLACEMENT_ATTEMPTS = 60


@dataclass
class Room:
    """A rectangular room. (x, y) is the top-left floor tile; w/h are floor dimensions."""

    x: int
    y: int
    w: int
    h: int
    description: str = ""
    visited: bool = False

    @property
    def x2(self) -> int:
        return self.x + self.w - 1

    @property
    def y2(self) -> int:
        return self.y + self.h - 1

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x <= self.x2 and self.y <= y <= self.y2

    def intersects(self, other: Room, padding: int = 2) -> bool:
        return (
            self.x - padding <= other.x2
            and self.x2 + padding >= other.x
            and self.y - padding <= other.y2
            and self.y2 + padding >= other.y
        )

    def random_point(self, rng: random.Random) -> tuple[int, int]:
        return (rng.randint(self.x, self.x2), rng.randint(self.y, self.y2))


class GameMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles = [[WALL] * width for _ in range(height)]
        self.explored = [[False] * width for _ in range(height)]
        self.visible = [[False] * width for _ in range(height)]
        self.rooms: list[Room] = []
        self.start: tuple[int, int] = (0, 0)
        self.stairs: tuple[int, int] = (0, 0)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile(self, x: int, y: int) -> str:
        return self.tiles[y][x] if self.in_bounds(x, y) else WALL

    def is_walkable(self, x: int, y: int) -> bool:
        return self.tile(x, y) != WALL

    def is_transparent(self, x: int, y: int) -> bool:
        return self.tile(x, y) != WALL

    def room_at(self, x: int, y: int) -> Room | None:
        for room in self.rooms:
            if room.contains(x, y):
                return room
        return None

    def is_wall_face(self, x: int, y: int) -> bool:
        """True for wall tiles that border a floor tile (the ones worth drawing)."""
        if self.tile(x, y) != WALL:
            return False
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if self.in_bounds(x + dx, y + dy) and self.tiles[y + dy][x + dx] != WALL:
                    return True
        return False

    # -- carving helpers -------------------------------------------------
    def carve_room(self, room: Room) -> None:
        for y in range(room.y, room.y2 + 1):
            for x in range(room.x, room.x2 + 1):
                self.tiles[y][x] = FLOOR

    def carve_h(self, x1: int, x2: int, y: int) -> None:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[y][x] = FLOOR

    def carve_v(self, y1: int, y2: int, x: int) -> None:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[y][x] = FLOOR

    def connect(self, a: Room, b: Room, rng: random.Random) -> None:
        (x1, y1), (x2, y2) = a.center, b.center
        if rng.random() < 0.5:
            self.carve_h(x1, x2, y1)
            self.carve_v(y1, y2, x2)
        else:
            self.carve_v(y1, y2, x1)
            self.carve_h(x1, x2, y2)


def generate_floor(rng: random.Random, width: int = MAP_WIDTH, height: int = MAP_HEIGHT) -> GameMap:
    """Build a floor of non-overlapping rooms, chained together plus a few extra loops."""
    while True:
        game_map = _try_generate(rng, width, height)
        if len(game_map.rooms) >= 4:
            return game_map


def _try_generate(rng: random.Random, width: int, height: int) -> GameMap:
    game_map = GameMap(width, height)

    for _ in range(PLACEMENT_ATTEMPTS):
        if len(game_map.rooms) >= MAX_ROOMS:
            break
        w = rng.randint(ROOM_MIN_W, ROOM_MAX_W)
        h = rng.randint(ROOM_MIN_H, ROOM_MAX_H)
        # Keep a one-tile wall border around the whole map.
        x = rng.randint(1, width - w - 1)
        y = rng.randint(1, height - h - 1)
        room = Room(x, y, w, h)
        if any(room.intersects(other) for other in game_map.rooms):
            continue
        game_map.carve_room(room)
        game_map.rooms.append(room)

    # Sorting left-to-right before chaining keeps corridors short and readable.
    game_map.rooms.sort(key=lambda r: r.center[0])
    for prev, room in zip(game_map.rooms, game_map.rooms[1:]):
        game_map.connect(prev, room, rng)
    # A couple of extra corridors create loops so fights aren't always in dead ends.
    for _ in range(max(1, len(game_map.rooms) // 4)):
        a, b = rng.sample(game_map.rooms, 2)
        game_map.connect(a, b, rng)

    # Start in one end room, stairs in whichever room lies farthest away.
    start_room = game_map.rooms[0] if rng.random() < 0.5 else game_map.rooms[-1]
    game_map.start = start_room.center
    sx, sy = game_map.start
    far_room = max(game_map.rooms, key=lambda r: abs(r.center[0] - sx) + abs(r.center[1] - sy))
    game_map.stairs = far_room.center
    stx, sty = game_map.stairs
    game_map.tiles[sty][stx] = STAIRS

    return game_map
