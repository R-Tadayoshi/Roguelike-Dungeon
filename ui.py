"""Terminal rendering and key handling with blessed."""

from __future__ import annotations

import os
import textwrap

from blessed import Terminal

from game import CONFIRM_QUIT, DEAD, HELP, HISTORY, INVENTORY, INVENTORY_SIZE
from map_gen import FLOOR, MAP_HEIGHT, MAP_WIDTH, STAIRS, WALL

SIDEBAR_X = MAP_WIDTH + 2
MIN_WIDTH = SIDEBAR_X + 28
MIN_HEIGHT = MAP_HEIGHT + 7

# Tile appearance: (char, style in view, style when only remembered).
TILE_STYLE = {
    WALL: ("#", "sienna", "gray27"),
    FLOOR: (".", "gray50", "gray19"),
    STAIRS: (">", "bold_white", "gray40"),
}


# On 16-color terminals blessed would round the dark grays down to black, hiding
# remembered map tiles, so substitute basic colors that stay readable.
FALLBACK_16 = {
    "gray19": "bright_black", "gray27": "bright_black", "gray30": "bright_black",
    "gray40": "bright_black", "gray46": "bright_black", "gray50": "white",
    "gray62": "white", "gray70": "white", "sienna": "yellow", "wheat": "yellow",
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
            self.draw_sidebar(canvas, game)
            self.draw_log(canvas, game)
            if game.mode == DEAD:
                self.draw_game_over(canvas, game)
            elif game.mode == INVENTORY:
                self.draw_inventory(canvas, game)
            elif game.mode == HELP:
                self.draw_help(canvas)
            elif game.mode == HISTORY:
                self.draw_history(canvas, game)
            elif game.mode == CONFIRM_QUIT:
                self.draw_box(canvas, [("Abandon this run and quit?", "bold_white"), ("", ""), ("[Y] quit    [N] keep playing", "bold_gold")])
        print(canvas.render(), end="", flush=True)

    def draw_map(self, canvas: Canvas, game) -> None:
        gm = game.game_map
        for y in range(gm.height):
            for x in range(gm.width):
                if not gm.explored[y][x]:
                    continue
                tile = gm.tiles[y][x]
                if tile == WALL and not gm.is_wall_face(x, y):
                    continue
                char, lit, remembered = TILE_STYLE[tile]
                canvas.put(x, y, char, lit if gm.visible[y][x] else remembered)
        for item in game.items:
            if gm.visible[item.y][item.x]:
                canvas.put(item.x, item.y, item.char, item.color)
        for m in game.visible_monsters():
            canvas.put(m.x, m.y, m.char, m.color)
        p = game.player
        canvas.put(p.x, p.y, p.char, p.color)

    def draw_status(self, canvas: Canvas, game) -> None:
        p = game.player
        y = MAP_HEIGHT
        x = 1
        canvas.put(x, y, "HP ", "bold_white")
        x += 3
        bar_style = hp_style(p.hp, p.max_hp)
        filled = round(12 * p.hp / p.max_hp)
        canvas.put(x, y, "█" * filled, bar_style)
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
            x += len(label) + len(value) + 4
        canvas.put(0, y + 1, "─" * (canvas.width - 1), "gray30")

    def draw_sidebar(self, canvas: Canvas, game) -> None:
        p = game.player
        x = SIDEBAR_X
        y = 0
        canvas.put(x, y, "THE ADVENTURER", "bold_gold")
        y += 1
        canvas.put(x, y, f"Attack  {p.attack:<4}Defense {p.defense}", "wheat")
        y += 2

        canvas.put(x, y, "IN SIGHT", "bold_gold")
        y += 1
        seen = game.visible_monsters()
        if not seen:
            canvas.put(x, y, "Nothing stirs.", "gray50")
            y += 1
        for m in seen[:6]:
            canvas.put(x, y, m.char, m.color)
            canvas.put(x + 2, y, m.name[:14], "white")
            filled = max(1, round(8 * m.hp / m.max_hp))
            canvas.put(x + 17, y, "█" * filled, hp_style(m.hp, m.max_hp))
            canvas.put(x + 17 + filled, y, "░" * (8 - filled), "gray27")
            y += 1
        y += 1

        canvas.put(x, y, f"PACK ({len(p.inventory)}/{INVENTORY_SIZE})", "bold_gold")
        y += 1
        groups = game.inventory_groups()
        if not groups:
            canvas.put(x, y, "Empty.", "gray50")
            y += 1
        for group in groups[:4]:
            item = group[0]
            canvas.put(x, y, item.char, item.color)
            count = f" x{len(group)}" if len(group) > 1 else ""
            canvas.put(x + 2, y, f"{item.name}{count}"[:26], "white")
            y += 1
        y += 1

        keys = [
            ("WASD/arrows", "move, attack"),
            ("g", "pick up"),
            ("i", "inventory"),
            (">", "descend stairs"),
            (". or space", "wait a turn"),
            ("m", "message history"),
            ("?", "help"),
            ("Esc", "quit"),
        ]
        y = max(y, MAP_HEIGHT - len(keys) - 1)
        canvas.put(x, y, "KEYS", "bold_gold")
        for i, (k, desc) in enumerate(keys):
            canvas.put(x, y + 1 + i, k, "bold_white")
            canvas.put(x + 12, y + 1 + i, desc, "gray62")

    def draw_game_over(self, canvas: Canvas, game) -> None:
        p = game.player
        tally = ", ".join(f"{n} {name}{'s' if n > 1 else ''}" for name, n in p.kills_by_kind.items())
        lines = [
            ("YOU HAVE DIED", "bold_red"),
            ("", ""),
            (f"You were {game.death_cause} on depth {game.depth}", "wheat"),
            (f"after {game.turn} turns in the dark.", "wheat"),
            ("", ""),
            (f"Depth reached:  {game.depth}".ljust(24), "white"),
            (f"Level reached:  {p.level}".ljust(24), "white"),
            (f"Monsters slain: {p.kills}".ljust(24), "white"),
        ]
        for line in textwrap.wrap(tally, 44):
            lines.append((line, "gray62"))
        lines += [("", ""), ("[R] descend again    [Q] quit", "bold_gold")]
        self.draw_box(canvas, lines)

    def draw_inventory(self, canvas: Canvas, game) -> None:
        lines = [("INVENTORY", "bold_gold"), ("", "")]
        groups = game.inventory_groups()
        if not groups:
            lines.append(("Your pack is empty.", "gray62"))
        for i, group in enumerate(groups):
            item = group[0]
            count = f" x{len(group)}" if len(group) > 1 else ""
            heal = f"  (+{item.template['amount']} HP)" if item.template["effect"] == "heal" else ""
            lines.append((f"{chr(ord('a') + i)}) {item.name}{count}{heal}".ljust(40), "white"))
        lines += [("", ""), ("Press a letter to use, Esc to close", "gray62")]
        self.draw_box(canvas, lines)

    def draw_help(self, canvas: Canvas) -> None:
        lines = [
            ("HOW TO PLAY", "bold_gold"),
            ("", ""),
            ("Find the stairs (>) and descend as deep as you dare.", "wheat"),
            ("Walk into a monster to attack it. Monsters act after you do.", "wheat"),
            ("", ""),
            ("WASD/arrows  move or attack    g   pick up item".ljust(58), "white"),
            ("> or Enter   descend stairs    i   inventory / drink".ljust(58), "white"),
            (". or space   wait a turn       m   message history".ljust(58), "white"),
            ("Esc          quit              ?   this help".ljust(58), "white"),
            ("", ""),
            ("@ you   r rat   g goblin   s skeleton   ! potion   > stairs", "gray62"),
            ("", ""),
            ("Press any key to return", "gray62"),
        ]
        self.draw_box(canvas, lines)

    def draw_history(self, canvas: Canvas, game) -> None:
        width, height = MAP_WIDTH - 6, MAP_HEIGHT - 6
        wrapped: list[tuple[str, str]] = []
        for msg in game.messages:
            for line in textwrap.wrap(message_text(msg), width) or [""]:
                wrapped.append((line.ljust(width), msg.color))
        end = max(height, len(wrapped) - game.history_offset)
        body = wrapped[max(0, end - height):end]
        body += [("".ljust(width), "")] * (height - len(body))
        lines = [("MESSAGE HISTORY", "bold_gold"), *body, ("", ""), ("Up/Down or W/S to scroll, Esc to close", "gray62")]
        self.draw_box(canvas, lines)

    def draw_box(self, canvas: Canvas, lines: list[tuple[str, str]]) -> None:
        """Draw a bordered, centered panel over the map."""
        inner = max(len(text) for text, _ in lines) + 4
        left = max(0, (MAP_WIDTH - inner - 2) // 2)
        top = max(0, (MAP_HEIGHT - len(lines) - 2) // 2)
        canvas.put(left, top, "╔" + "═" * inner + "╗", "gold")
        for i, (text, style) in enumerate(lines):
            row = top + 1 + i
            canvas.put(left, row, "║" + " " * inner + "║", "gold")
            canvas.put(left + 1 + (inner - len(text)) // 2, row, text, style)
        canvas.put(left, top + len(lines) + 1, "╚" + "═" * inner + "╝", "gold")

    def draw_log(self, canvas: Canvas, game) -> None:
        top = MAP_HEIGHT + 2
        height = canvas.height - top
        width = canvas.width - 2
        lines: list[tuple[str, str]] = []
        for msg in game.messages[-height:]:
            # Messages from the latest turn are in full color; older ones fade to gray.
            fresh = msg.turn >= game.turn - 1
            for line in textwrap.wrap(message_text(msg), width) or [""]:
                lines.append((line, msg.color if fresh else "gray46"))
        for i, (line, style) in enumerate(lines[-height:]):
            canvas.put(1, top + i, line, style)


def message_text(msg) -> str:
    return msg.text if msg.count == 1 else f"{msg.text} (x{msg.count})"


MOVE_KEYS = {
    "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
    "KEY_UP": (0, -1), "KEY_DOWN": (0, 1), "KEY_LEFT": (-1, 0), "KEY_RIGHT": (1, 0),
}


def key_to_action(key, mode: str) -> tuple | None:
    """Translate a blessed keystroke into a game action tuple for the current mode."""
    name = key.name if key.is_sequence else str(key).lower()
    if mode == DEAD:
        if name == "r":
            return ("restart",)
        if name in ("q", "KEY_ESCAPE"):
            return ("quit",)
        return None
    if mode == CONFIRM_QUIT:
        return ("quit",) if name == "y" else ("close",)
    if mode == HELP:
        return ("close",)
    if mode == HISTORY:
        if name in ("KEY_UP", "w"):
            return ("scroll", 1)
        if name in ("KEY_DOWN", "s"):
            return ("scroll", -1)
        if name == "KEY_PGUP":
            return ("scroll", 10)
        if name == "KEY_PGDOWN":
            return ("scroll", -10)
        if name in ("KEY_ESCAPE", "m", "q"):
            return ("close",)
        return None
    if mode == INVENTORY:
        if name in ("KEY_ESCAPE", "i", "q"):
            return ("close",)
        if len(name) == 1 and "a" <= name <= "z":
            return ("use", ord(name) - ord("a"))
        return None

    if name in MOVE_KEYS:
        return ("move", *MOVE_KEYS[name])
    if name in (".", " "):
        return ("wait",)
    if name == "g":
        return ("pickup",)
    if name == "i":
        return ("open", INVENTORY)
    if name == "m":
        return ("open", HISTORY)
    if name == "?":
        return ("open", HELP)
    if name in (">", "KEY_ENTER"):
        return ("descend",)
    if name == "KEY_ESCAPE" or str(key) == "Q":
        return ("open", CONFIRM_QUIT)
    return None
