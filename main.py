"""Entry point: python main.py"""

from __future__ import annotations

import argparse
import sys

from game import Game
from ui import Renderer, key_to_action, make_terminal


def run(seed: int | None = None) -> None:
    term = make_terminal()
    game = Game(seed)
    renderer = Renderer(term)
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        size = None
        dirty = True
        while game.running:
            if (term.width, term.height) != size:
                size = (term.width, term.height)
                print(term.clear, end="")
                dirty = True
            if dirty:
                renderer.draw(game)
                dirty = False
            # Short timeout so window resizes are noticed (Windows has no SIGWINCH).
            key = term.inkey(timeout=0.25, esc_delay=0.05)
            if not key:
                continue
            action = key_to_action(key, game.mode)
            if action:
                game.handle(action)
                dirty = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A medieval fantasy roguelike for the terminal.")
    parser.add_argument("--seed", type=int, help="seed the dungeon generator for a repeatable run")
    args = parser.parse_args()
    try:
        run(args.seed)
    except KeyboardInterrupt:
        sys.exit(0)
