"""Game state and turn logic. Knows nothing about the terminal; ui.py draws it."""

from __future__ import annotations

import random
from dataclasses import dataclass

import ai
from combat import describe_monster_attack, describe_player_attack, resolve_attack
from data import combat_text
from data.monsters import MONSTERS
from entities import Monster, Player
from fov import compute_fov
from map_gen import generate_floor

# Modes decide how keys are interpreted and what the UI draws on top of the map.
PLAYING = "playing"
DEAD = "dead"


@dataclass
class Message:
    text: str
    color: str = "white"
    count: int = 1
    turn: int = 0


def pick_by_depth(table: dict, depth: int, rng: random.Random) -> str | None:
    """Weighted pick from a {key: {"spawn": [(min_depth, weight), ...]}} table."""
    keys, weights = [], []
    for key, entry in table.items():
        weight = 0
        for min_depth, w in entry["spawn"]:
            if depth >= min_depth:
                weight = w
        if weight > 0:
            keys.append(key)
            weights.append(weight)
    return rng.choices(keys, weights)[0] if keys else None


class Game:
    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)
        self.new_game()

    def new_game(self) -> None:
        self.depth = 1
        self.turn = 0
        self.messages: list[Message] = []
        self.player = Player(0, 0)
        self.monsters: list[Monster] = []
        self.mode = PLAYING
        self.running = True
        self.death_cause = ""
        self.build_floor()
        self.log("You descend into the dungeon. Use WASD or the arrow keys to move.", "gold")

    def build_floor(self) -> None:
        self.game_map = generate_floor(self.rng)
        self.player.x, self.player.y = self.game_map.start
        self.monsters = []
        self.spawn_monsters()
        self.update_fov()

    def spawn_monsters(self) -> None:
        max_per_room = min(1 + self.depth // 2, 4)
        for room in self.game_map.rooms:
            if room.contains(*self.game_map.start):
                continue  # A quiet first room gives the player a moment to breathe.
            for _ in range(self.rng.randint(0, max_per_room)):
                x, y = room.random_point(self.rng)
                if self.is_blocked(x, y) or (x, y) == self.game_map.stairs:
                    continue
                kind = pick_by_depth(MONSTERS, self.depth, self.rng)
                self.monsters.append(Monster(x, y, kind, MONSTERS[kind], self.depth))

    def update_fov(self) -> None:
        compute_fov(self.game_map, self.player.x, self.player.y)

    # -- queries ---------------------------------------------------------
    def monster_at(self, x: int, y: int) -> Monster | None:
        for m in self.monsters:
            if m.x == x and m.y == y:
                return m
        return None

    def is_blocked(self, x: int, y: int) -> bool:
        if not self.game_map.is_walkable(x, y):
            return True
        if self.player.pos == (x, y):
            return True
        return self.monster_at(x, y) is not None

    def visible_monsters(self) -> list[Monster]:
        vis = self.game_map.visible
        return [m for m in self.monsters if vis[m.y][m.x]]

    # -- messages --------------------------------------------------------
    def log(self, text: str, color: str = "white") -> None:
        last = self.messages[-1] if self.messages else None
        if last and last.text == text and last.turn == self.turn:
            last.count += 1
        else:
            self.messages.append(Message(text, color, turn=self.turn))

    # -- actions ---------------------------------------------------------
    def handle(self, action: tuple) -> None:
        kind = action[0]
        if kind == "quit":
            self.running = False
        elif kind == "restart":
            self.new_game()
        elif self.mode != PLAYING:
            return
        elif kind == "move":
            self.try_move(action[1], action[2])
        elif kind == "wait":
            self.end_turn()

    def try_move(self, dx: int, dy: int) -> None:
        nx, ny = self.player.x + dx, self.player.y + dy
        target = self.monster_at(nx, ny)
        if target:
            self.player_attack(target)
            self.end_turn()
            return
        if not self.game_map.is_walkable(nx, ny):
            return  # Bumping a wall costs no turn.
        self.player.x, self.player.y = nx, ny
        self.update_fov()
        self.end_turn()

    def player_attack(self, monster: Monster) -> None:
        result = resolve_attack(self.rng, self.player, monster)
        self.log(*describe_player_attack(self.rng, result, monster))
        if result.killed:
            self.kill_monster(monster)

    def kill_monster(self, monster: Monster) -> None:
        self.monsters.remove(monster)
        self.player.kills += 1
        self.log(self.rng.choice(monster.template["death"]), "gold")
        if self.player.gain_xp(monster.xp):
            self.log(combat_text.LEVEL_UP.format(level=self.player.level), "bold_cyan")

    def monster_attack(self, monster: Monster) -> None:
        result = resolve_attack(self.rng, monster, self.player)
        self.log(*describe_monster_attack(self.rng, result, monster))
        if result.killed:
            self.death_cause = f"slain by a {monster.name}"
            self.log(combat_text.PLAYER_DEATH, "bold_red")
            self.mode = DEAD

    def end_turn(self) -> None:
        """Everything that happens after the player acts: monsters move, the clock ticks."""
        dist_cache: dict = {}
        for monster in list(self.monsters):
            if self.mode == DEAD:
                break
            ai.take_turn(self, monster, dist_cache)
        self.turn += 1
