"""Terminal rendering and line input with blessed.

Layout:
    status bar (HP, depth, level, XP, kills)
    ───────────────────────────────────────────
    story / message log           │ sidebar: room map,
    (scrolls, newest at bottom)   │ monsters here, pack
    ───────────────────────────────────────────
    > command line
"""

from __future__ import annotations

import os
import textwrap

from blessed import Terminal

from game import CONFIRM_QUIT, DEAD, INVENTORY_SIZE
from map_gen import GRID_HEIGHT

SIDEBAR_WIDTH = 30
MIN_WIDTH = 80
MIN_HEIGHT = 24

# On 16-color terminals blessed would round the dark grays down to black, hiding
# text, so substitute basic colors that stay readable.
FALLBACK_16 = {
    "gray27": "bright_black", "gray30": "bright_black", "gray40": "bright_black",
    "gray50": "bright_black", "gray62": "white", "gray70": "white",
    "wheat": "yellow", "orchid": "magenta", "orange": "yellow", "tan": "yellow",
}


def make_terminal() -> Terminal:
    term = Terminal()
    # Windows Terminal supports 24-bit color but does not always advertise it.
    truecolor = os.environ.get("WT_SESSION") or os.environ.get("COLORTERM") in ("truecolor", "24bit")
    if truecolor and term.does_styling and term.number_of_colors < 1 << 24:
        term.number_of_colors = 1 << 24
    return term


def hp_style(hp: int, max_hp: int) -> str:
    ratio = hp / max_hp
    if ratio > 0.5:
        return "green"
    if ratio > 0.25:
        return "yellow"
    return "red"


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
            name = style
            if self.term.number_of_colors < 256:
                name = FALLBACK_16.get(style, style)
            self._cache[style] = str(getattr(self.term, name)) if name else ""
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


class LineEditor:
    """The command line: typing, backspace, Enter, and Up/Down through earlier commands."""

    MAX_LENGTH = 60

    def __init__(self):
        self.buffer = ""
        self.history: list[str] = []
        self.history_pos = 0

    def handle(self, key) -> str | None:
        """Process one keystroke. Returns the submitted line when Enter is pressed."""
        name = key.name if key.is_sequence else None
        if name == "KEY_ENTER" or str(key) in ("\r", "\n"):
            line, self.buffer = self.buffer.strip(), ""
            if line and (not self.history or self.history[-1] != line):
                self.history.append(line)
            self.history_pos = len(self.history)
            return line
        if name in ("KEY_BACKSPACE", "KEY_DELETE") or str(key) in ("\x08", "\x7f"):
            self.buffer = self.buffer[:-1]
        elif name == "KEY_ESCAPE":
            self.buffer = ""
        elif name == "KEY_UP" and self.history:
            self.history_pos = max(0, self.history_pos - 1)
            self.buffer = self.history[self.history_pos]
        elif name == "KEY_DOWN" and self.history:
            self.history_pos = min(len(self.history), self.history_pos + 1)
            self.buffer = self.history[self.history_pos] if self.history_pos < len(self.history) else ""
        elif not key.is_sequence and str(key).isprintable() and len(self.buffer) < self.MAX_LENGTH:
            self.buffer += str(key)
        return None


class Renderer:
    def __init__(self, term: Terminal):
        self.term = term
        self.scroll = 0  # Lines scrolled up from the newest message.

    def too_small(self) -> bool:
        return self.term.width < MIN_WIDTH or self.term.height < MIN_HEIGHT

    def page(self) -> int:
        return max(1, self.term.height - 6)

    def draw(self, game, editor: LineEditor) -> None:
        t = self.term
        canvas = Canvas(t, t.width, t.height)
        if self.too_small():
            msg = f"Please enlarge the window to at least {MIN_WIDTH}x{MIN_HEIGHT} (now {t.width}x{t.height})."
            for i, line in enumerate(textwrap.wrap(msg, max(10, t.width - 2))):
                canvas.put(1, 1 + i, line, "bold_red")
        else:
            story_width = canvas.width - SIDEBAR_WIDTH - 2
            self.draw_status(canvas, game)
            canvas.put(0, 1, "─" * canvas.width, "gray30")
            canvas.put(0, canvas.height - 2, "─" * canvas.width, "gray30")
            for y in range(2, canvas.height - 2):
                canvas.put(story_width, y, "│", "gray30")
            self.draw_story(canvas, game, story_width)
            self.draw_sidebar(canvas, game, story_width + 2)
            self.draw_prompt(canvas, game, editor)
            if game.mode == DEAD:
                self.draw_game_over(canvas, game, story_width)
        print(canvas.render(), end="", flush=True)

    def draw_status(self, canvas: Canvas, game) -> None:
        p = game.player
        x, y = 1, 0
        canvas.put(x, y, "HP ", "bold_white")
        x += 3
        filled = round(12 * p.hp / p.max_hp)
        canvas.put(x, y, "█" * filled, hp_style(p.hp, p.max_hp))
        canvas.put(x + filled, y, "░" * (12 - filled), "gray27")
        x += 13
        for label, value in (
            ("", f"{p.hp}/{p.max_hp}"),
            ("Depth ", str(game.depth)),
            ("Level ", str(p.level)),
            ("XP ", f"{p.xp}/{p.xp_to_next}"),
            ("Kills ", str(p.kills)),
        ):
            canvas.put(x, y, label, "gray62")
            canvas.put(x + len(label), y, value, "bold_white")
            x += len(label) + len(value) + 3

    def draw_story(self, canvas: Canvas, game, width: int) -> None:
        top, bottom = 2, canvas.height - 3
        height = bottom - top + 1
        # Wrap from the newest message backwards, only as far as the screen can show.
        lines: list[tuple[str, str]] = []
        index = len(game.messages)
        while index > 0 and len(lines) < height + self.scroll:
            index -= 1
            msg = game.messages[index]
            # The latest command's results are in full color; older story fades.
            style = msg.color if index >= game.fresh_from else "gray50"
            lines[:0] = [(line, style) for line in textwrap.wrap(msg.text, width - 2) or [""]]
        self.scroll = max(0, min(self.scroll, len(lines) - height))
        end = len(lines) - self.scroll
        for i, (line, style) in enumerate(lines[max(0, end - height):end]):
            canvas.put(1, top + i, line, style)
        if self.scroll:
            canvas.put(width - 15, bottom, " more below ↓ ", "reverse")

    def draw_sidebar(self, canvas: Canvas, game, x: int) -> None:
        p = game.player
        y = 2
        bottom = canvas.height - 3
        canvas.put(x, y, f"ATTACK {p.attack}   DEFENSE {p.defense}", "wheat")
        y += 1
        canvas.put(x, y, f"MAP OF DEPTH {game.depth}", "bold_gold")
        y = self.draw_map(canvas, game, x, y + 1)
        for dx, text, style in ((0, "@", "bold_yellow"), (1, " you", "gray62"),
                                (7, ">", "bold_white"), (8, " stairs", "gray62"),
                                (17, "?", "gray50"), (18, " unknown", "gray62")):
            canvas.put(x + dx, y, text, style)
        y += 2

        canvas.put(x, y, "HERE", "bold_gold")
        y += 1
        if not game.room.monsters:
            canvas.put(x, y, "No enemies.", "gray50")
            y += 1
        for i, m in enumerate(game.room.monsters[:4], 1):
            if y > bottom:
                return
            canvas.put(x, y, f"{i} ", "gray62")
            canvas.put(x + 2, y, m.name[:14], m.color)
            filled = max(1, round(8 * m.hp / m.max_hp))
            canvas.put(x + 18, y, "█" * filled, hp_style(m.hp, m.max_hp))
            canvas.put(x + 18 + filled, y, "░" * (8 - filled), "gray27")
            y += 1
        y += 1
        if y >= bottom:
            return

        canvas.put(x, y, f"PACK ({len(p.inventory)}/{INVENTORY_SIZE})", "bold_gold")
        y += 1
        groups: dict[str, list] = {}
        for item in p.inventory:
            groups.setdefault(item.name, []).append(item)
        if not groups:
            canvas.put(x, y, "Empty.", "gray50")
        for name, items in groups.items():
            if y > bottom:
                return
            canvas.put(x, y, "!", items[0].color)
            canvas.put(x + 2, y, f"{name} x{len(items)}"[:SIDEBAR_WIDTH - 2], "white")
            y += 1

    def draw_map(self, canvas: Canvas, game, left: int, top: int) -> int:
        """Draw visited rooms as [ ] boxes joined by doorways; return the next free row."""
        floor = game.floor
        visited = [r for r in floor.rooms if r.visited]
        seen = {n for r in visited for n in r.exits.values() if not n.visited}
        for room in seen:
            canvas.put(left + room.gx * 4, top + room.gy * 2, "[?]", "gray40")
        for room in visited:
            x, y = left + room.gx * 4, top + room.gy * 2
            canvas.put(x, y, "[ ]", "gray70")
            if room is game.room:
                canvas.put(x + 1, y, "@", "bold_yellow")
            elif room.stairs:
                canvas.put(x + 1, y, ">", "bold_white")
            elif room.items:
                canvas.put(x + 1, y, "!", "bold_red")
            # Doorways sit in the gap between two boxes.
            if "east" in room.exits:
                canvas.put(x + 3, y, "-", "gray62")
            if "west" in room.exits:
                canvas.put(x - 1, y, "-", "gray62")
            if "south" in room.exits:
                canvas.put(x + 1, y + 1, "|", "gray62")
            if "north" in room.exits:
                canvas.put(x + 1, y - 1, "|", "gray62")
        return top + GRID_HEIGHT * 2 - 1

    def draw_prompt(self, canvas: Canvas, game, editor: LineEditor) -> None:
        y = canvas.height - 1
        prompt = {DEAD: "(restart/quit) > ", CONFIRM_QUIT: "(yes/no) > "}.get(game.mode, "> ")
        canvas.put(1, y, prompt, "bold_cyan")
        canvas.put(1 + len(prompt), y, editor.buffer, "white")
        canvas.put(1 + len(prompt) + len(editor.buffer), y, " ", "reverse")

    def draw_game_over(self, canvas: Canvas, game, story_width: int) -> None:
        p = game.player
        tally = ", ".join(f"{n} {name}{'s' if n > 1 else ''}" for name, n in p.kills_by_kind.items())
        lines = [
            ("YOU HAVE DIED", "bold_red"),
            ("", ""),
            (f"You were {game.death_cause}", "wheat"),
            (f"on depth {game.depth}, after {game.turn} turns.", "wheat"),
            ("", ""),
            (f"Depth reached:  {game.depth}".ljust(22), "white"),
            (f"Level reached:  {p.level}".ljust(22), "white"),
            (f"Monsters slain: {p.kills}".ljust(22), "white"),
        ]
        for line in textwrap.wrap(tally, story_width - 10):
            lines.append((line, "gray62"))
        lines += [("", ""), ("Type 'restart' or 'quit'", "bold_gold")]

        inner = min(story_width - 4, max(len(text) for text, _ in lines) + 4)
        left = max(0, (story_width - inner - 2) // 2)
        top = max(2, (canvas.height - len(lines) - 2) // 2)
        canvas.put(left, top, "╔" + "═" * inner + "╗", "gold")
        for i, (text, style) in enumerate(lines):
            row = top + 1 + i
            canvas.put(left, row, "║" + " " * inner + "║", "gold")
            canvas.put(left + 1 + (inner - len(text)) // 2, row, text, style)
        canvas.put(left, top + len(lines) + 1, "╚" + "═" * inner + "╝", "gold")
