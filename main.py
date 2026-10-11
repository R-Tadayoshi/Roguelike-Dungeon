"""Entry point: python main.py"""

from __future__ import annotations

import sys

from blessed import Terminal

from game import Game
from ui import Renderer, key_to_action


def run() -> None:
    term = Terminal()
    game = Game()
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
    try:
        run()
    except KeyboardInterrupt:
        sys.exit(0)
