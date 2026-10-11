"""Game state and turn logic. Knows nothing about the terminal; ui.py draws it."""

from __future__ import annotations

import random
from dataclasses import dataclass

from entities import Player
from fov import compute_fov
from map_gen import generate_floor


@dataclass
class Message:
    text: str
    color: str = "white"
    count: int = 1
    turn: int = 0


class Game:
    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)
        self.new_game()

    def new_game(self) -> None:
        self.depth = 1
        self.turn = 0
        self.messages: list[Message] = []
        self.player = Player(0, 0)
        self.running = True
        self.build_floor()
        self.log("You descend into the dungeon. Use WASD or the arrow keys to move.", "gold")

    def build_floor(self) -> None:
        self.game_map = generate_floor(self.rng)
        self.player.x, self.player.y = self.game_map.start
        self.update_fov()

    def update_fov(self) -> None:
        compute_fov(self.game_map, self.player.x, self.player.y)

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
        if kind == "move":
            self.try_move(action[1], action[2])
        elif kind == "quit":
            self.running = False

    def try_move(self, dx: int, dy: int) -> None:
        nx, ny = self.player.x + dx, self.player.y + dy
        if not self.game_map.is_walkable(nx, ny):
            return  # Bumping a wall costs no turn.
        self.player.x, self.player.y = nx, ny
        self.update_fov()
        self.end_turn()

    def end_turn(self) -> None:
        self.turn += 1
