"""Terminal rendering and key handling with blessed."""

from __future__ import annotations

import textwrap

from blessed import Terminal

from map_gen import FLOOR, MAP_HEIGHT, MAP_WIDTH, STAIRS, WALL

SIDEBAR_X = MAP_WIDTH + 2
MIN_WIDTH = SIDEBAR_X + 28
MIN_HEIGHT = MAP_HEIGHT + 7

# Tile appearance: (char, lit style).
TILE_STYLE = {
    WALL: ("#", "sienna"),
    FLOOR: (".", "gray50"),
    STAIRS: (">", "bold_white"),
}


class Canvas:
    """An off-screen character grid. Drawing the whole frame in one write avoids flicker."""

    def __init__(self, term: Terminal, width: int, height: int):
        self.term = term
        self.width = width
        self.height = height
        self.chars = [[" "] * width for _ in range(height)]
        self.styles = [[""] * width for _ in range(height)]
        self._cache: dict[str, str] = {}

    def seq(self, style: str) -> str:
        if style not in self._cache:
            self._cache[style] = str(getattr(self.term, style)) if style else ""
        return self._cache[style]

    def put(self, x: int, y: int, text: str, style: str = "") -> None:
        if not 0 <= y < self.height:
            return
        for i, ch in enumerate(text):
            if 0 <= x + i < self.width:
                self.chars[y][x + i] = ch
                self.styles[y][x + i] = style

    def render(self) -> str:
        t = self.term
        out = []
        for y in range(self.height):
            # Never write the bottom-right cell: some terminals scroll when you do.
            width = self.width - 1 if y == self.height - 1 else self.width
            out.append(t.move_xy(0, y))
            current = None
            for x in range(width):
                style = self.styles[y][x]
                if style != current:
                    out.append(t.normal + self.seq(style))
                    current = style
                out.append(self.chars[y][x])
            out.append(t.normal)
        return "".join(out)


class Renderer:
    def __init__(self, term: Terminal):
        self.term = term

    def too_small(self) -> bool:
        return self.term.width < MIN_WIDTH or self.term.height < MIN_HEIGHT

    def draw(self, game) -> None:
        t = self.term
        canvas = Canvas(t, t.width, t.height)
        if self.too_small():
            msg = f"Please enlarge the window to at least {MIN_WIDTH}x{MIN_HEIGHT} (now {t.width}x{t.height})."
            for i, line in enumerate(textwrap.wrap(msg, max(10, t.width - 2))):
                canvas.put(1, 1 + i, line, "bold_red")
        else:
            self.draw_map(canvas, game)
            self.draw_status(canvas, game)
            self.draw_log(canvas, game)
        print(canvas.render(), end="", flush=True)

    def draw_map(self, canvas: Canvas, game) -> None:
        gm = game.game_map
        for y in range(gm.height):
            for x in range(gm.width):
                tile = gm.tiles[y][x]
                if tile == WALL and not gm.is_wall_face(x, y):
                    continue
                char, style = TILE_STYLE[tile]
                canvas.put(x, y, char, style)
        p = game.player
        canvas.put(p.x, p.y, p.char, p.color)

    def draw_status(self, canvas: Canvas, game) -> None:
        p = game.player
        y = MAP_HEIGHT
        canvas.put(0, y, f" HP {p.hp}/{p.max_hp}", "bold_white")
        canvas.put(20, y, f"Depth {game.depth}", "bold_white")
        canvas.put(0, y + 1, "─" * (canvas.width - 1), "gray30")

    def draw_log(self, canvas: Canvas, game) -> None:
        top = MAP_HEIGHT + 2
        height = canvas.height - top
        width = canvas.width - 2
        lines: list[tuple[str, str]] = []
        for msg in game.messages[-height:]:
            text = msg.text if msg.count == 1 else f"{msg.text} (x{msg.count})"
            for line in textwrap.wrap(text, width) or [""]:
                lines.append((line, msg.color))
        for i, (line, style) in enumerate(lines[-height:]):
            canvas.put(1, top + i, line, style)


MOVE_KEYS = {
    "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
    "KEY_UP": (0, -1), "KEY_DOWN": (0, 1), "KEY_LEFT": (-1, 0), "KEY_RIGHT": (1, 0),
}


def key_to_action(key) -> tuple | None:
    """Translate a blessed keystroke into a game action tuple."""
    name = key.name if key.is_sequence else str(key).lower()
    if name in MOVE_KEYS:
        return ("move", *MOVE_KEYS[name])
    if name == "KEY_ESCAPE" or str(key) == "Q":
        return ("quit",)
    return None
