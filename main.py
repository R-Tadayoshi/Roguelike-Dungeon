"""Entry point: python main.py"""

from __future__ import annotations

import argparse
import os
import sys

try:
    import blessed  # noqa: F401
except ImportError:
    sys.exit(
        "The 'blessed' library is not installed for this Python.\n"
        "From the project folder, run:\n\n"
        f'    "{sys.executable}" -m pip install -r requirements.txt\n\n'
        "then start the game again with: python main.py"
    )

from game import Game  # noqa: E402
from ui import LineEditor, Renderer, make_terminal  # noqa: E402


def run(seed: int | None = None, use_color: bool = True) -> None:
    term = make_terminal()
    game = Game(seed, use_color)
    renderer = Renderer(term)
    editor = LineEditor()
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        size = None
        dirty = True
        while game.running:
            if (term.width, term.height) != size:
                size = (term.width, term.height)
                print(term.clear, end="")
                dirty = True
            if dirty:
                renderer.draw(game, editor)
                dirty = False
            # Short timeout so window resizes are noticed (Windows has no SIGWINCH).
            key = term.inkey(timeout=0.25, esc_delay=0.05)
            if not key:
                continue
            dirty = True
            if key.name == "KEY_PGUP":
                renderer.scroll += renderer.page()
            elif key.name == "KEY_PGDOWN":
                renderer.scroll = max(0, renderer.scroll - renderer.page())
            else:
                line = editor.handle(key)
                if line:
                    renderer.scroll = 0
                    game.submit(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A medieval fantasy text adventure roguelike for the terminal.")
    parser.add_argument("--seed", type=int, help="seed the dungeon generator for a repeatable run")
    parser.add_argument("--no-color", action="store_true", help="play without colors (also set by NO_COLOR)")
    args = parser.parse_args()
    # https://no-color.org: any non-empty NO_COLOR value turns colors off.
    use_color = not (args.no_color or os.environ.get("NO_COLOR"))
    try:
        run(args.seed, use_color)
    except KeyboardInterrupt:
        sys.exit(0)
