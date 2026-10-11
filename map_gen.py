"""Procedural dungeon floors: a network of named rooms laid out on a small grid.

Rooms sit on grid cells and connect to neighbouring cells through exits
(north/south/east/west). The grid only exists to give the floor a sensible
shape and to draw the sidebar map; the player never walks tile by tile.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field

GRID_WIDTH = 6
GRID_HEIGHT = 4

DIRECTIONS = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}


@dataclass(eq=False)
class Room:
    gx: int
    gy: int
    name: str = ""
    description: str = ""
    exits: dict[str, Room] = field(default_factory=dict)
    monsters: list = field(default_factory=list)
    items: list = field(default_factory=list)
    stairs: bool = False
    visited: bool = False


class Floor:
    def __init__(self, rooms: list[Room], start: Room):
        self.rooms = rooms
        self.start = start
        self._by_cell = {(r.gx, r.gy): r for r in rooms}

    def room_at(self, gx: int, gy: int) -> Room | None:
        return self._by_cell.get((gx, gy))

    @property
    def stairs_room(self) -> Room:
        return next(r for r in self.rooms if r.stairs)


def link(a: Room, b: Room) -> None:
    for direction, (dx, dy) in DIRECTIONS.items():
        if (a.gx + dx, a.gy + dy) == (b.gx, b.gy):
            a.exits[direction] = b
            b.exits[OPPOSITE[direction]] = a
            return
    raise ValueError("rooms are not adjacent")


def room_count(depth: int) -> int:
    return min(6 + depth, GRID_WIDTH * GRID_HEIGHT // 2 + 2)


def distances_from(start: Room) -> dict[Room, int]:
    dist = {start: 0}
    queue = deque([start])
    while queue:
        room = queue.popleft()
        for nxt in room.exits.values():
            if nxt not in dist:
                dist[nxt] = dist[room] + 1
                queue.append(nxt)
    return dist


def generate_floor(rng: random.Random, depth: int, room_texts: list[dict]) -> Floor:
    """Grow a connected set of rooms from a random cell, then add a few loops."""
    target = room_count(depth)
    start = Room(rng.randrange(GRID_WIDTH), rng.randrange(GRID_HEIGHT))
    cells = {(start.gx, start.gy): start}
    rooms = [start]

    while len(rooms) < target:
        parent = rng.choice(rooms)
        dx, dy = rng.choice(list(DIRECTIONS.values()))
        gx, gy = parent.gx + dx, parent.gy + dy
        if not (0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT) or (gx, gy) in cells:
            continue
        room = Room(gx, gy)
        cells[(gx, gy)] = room
        rooms.append(room)
        link(parent, room)

    # Extra doorways between neighbouring rooms make loops, so fleeing isn't always a dead end.
    for room in rooms:
        for direction, (dx, dy) in DIRECTIONS.items():
            other = cells.get((room.gx + dx, room.gy + dy))
            if other and direction not in room.exits and rng.random() < 0.2:
                link(room, other)

    for room, text in zip(rooms, rng.sample(room_texts, len(rooms))):
        room.name = text["name"]
        room.description = text["description"]

    # Stairs go in whichever room is the most doorways away from the start.
    dist = distances_from(start)
    far = max(rooms, key=lambda r: (dist[r], rng.random()))
    far.stairs = True
    return Floor(rooms, start)
