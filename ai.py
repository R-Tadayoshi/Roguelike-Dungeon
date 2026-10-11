"""Monster behaviour: notice the player, chase them, and attack when adjacent."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from entities import Monster
from map_gen import GameMap

if TYPE_CHECKING:
    from game import Game

DIRECTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0)]
ERRATIC_CHANCE = 0.3
UNREACHABLE = 10**9


def distance_map(game_map: GameMap, target: tuple[int, int]) -> list[list[int]]:
    """Walking distance from every tile to `target` (4-directional, walls only)."""
    dist = [[UNREACHABLE] * game_map.width for _ in range(game_map.height)]
    tx, ty = target
    dist[ty][tx] = 0
    queue = deque([target])
    while queue:
        x, y = queue.popleft()
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if game_map.is_walkable(nx, ny) and dist[ny][nx] == UNREACHABLE:
                dist[ny][nx] = dist[y][x] + 1
                queue.append((nx, ny))
    return dist


def take_turn(game: Game, monster: Monster, dist_cache: dict) -> None:
    player = game.player
    gm = game.game_map

    # FOV is symmetric enough: if the player can see the monster, it can see the player.
    if gm.visible[monster.y][monster.x]:
        if not monster.alerted:
            monster.alerted = True
            game.log(game.rng.choice(monster.template["notice"]), "orange")
        monster.last_seen = player.pos
    if not monster.alerted or monster.last_seen is None:
        return

    if abs(monster.x - player.x) + abs(monster.y - player.y) == 1:
        game.monster_attack(monster)
        return

    if monster.ai == "erratic" and game.rng.random() < ERRATIC_CHANCE:
        dx, dy = game.rng.choice(DIRECTIONS)
        if not game.is_blocked(monster.x + dx, monster.y + dy):
            monster.x += dx
            monster.y += dy
        return

    target = monster.last_seen
    if target not in dist_cache:
        dist_cache[target] = distance_map(gm, target)
    dist = dist_cache[target]

    best, best_d = None, dist[monster.y][monster.x]
    for dx, dy in DIRECTIONS:
        nx, ny = monster.x + dx, monster.y + dy
        if dist[ny][nx] < best_d and not game.is_blocked(nx, ny):
            best, best_d = (nx, ny), dist[ny][nx]
    if best:
        monster.x, monster.y = best

    # Reached the spot where the player was last seen and they're gone: give up.
    if monster.pos == target and not gm.visible[monster.y][monster.x]:
        monster.alerted = False
        monster.last_seen = None
