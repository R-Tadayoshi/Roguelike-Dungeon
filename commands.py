"""Turns typed text like "attack the goblin" or "n" into a (verb, target) command."""

from __future__ import annotations

from dataclasses import dataclass

# Every word the player might type for a command, mapped to the game's verb.
VERBS = {
    "go": "go", "walk": "go", "move": "go", "head": "go", "enter": "go",
    "attack": "attack", "a": "attack", "kill": "attack", "fight": "attack",
    "hit": "attack", "strike": "attack", "stab": "attack", "slash": "attack",
    "take": "take", "get": "take", "g": "take", "grab": "take", "pick": "take",
    "drink": "drink", "quaff": "drink", "use": "drink", "heal": "drink",
    "look": "look", "l": "look", "examine": "look",
    "inventory": "inventory", "inv": "inventory", "i": "inventory",
    "wait": "wait", "z": "wait",
    "rest": "rest", "sleep": "rest",
    "descend": "descend", "down": "descend", "d": "descend", ">": "descend",
    "stats": "stats", "status": "stats", "me": "stats",
    "help": "help", "?": "help", "h": "help", "commands": "help",
    "quit": "quit", "exit": "quit", "q": "quit",
}

DIRECTION_WORDS = {
    "n": "north", "north": "north",
    "s": "south", "south": "south",
    "e": "east", "east": "east",
    "w": "west", "west": "west",
}

# Little words that carry no meaning: "attack the goblin", "go to the north", "pick up a potion".
FILLER = {"the", "a", "an", "to", "at", "up", "on", "with", "from", "into", "toward", "towards", "my"}


@dataclass
class Command:
    verb: str
    target: str = ""


def parse(text: str) -> Command | None:
    """Return the command for `text`, or None if it doesn't start with a known verb or direction."""
    words = text.lower().replace(",", " ").replace(".", " ").split()
    if not words:
        return None
    first, rest = words[0], words[1:]

    if first in DIRECTION_WORDS and not rest:
        return Command("go", DIRECTION_WORDS[first])
    if first not in VERBS:
        return None

    verb = VERBS[first]
    # "a" is both the attack shortcut and an article; only the first word counts as the verb.
    target_words = [w for w in rest if w not in FILLER]
    target = " ".join(target_words)
    if verb == "go":
        if target in ("down", "d", "stairs", "downstairs"):
            return Command("descend")
        target = DIRECTION_WORDS.get(target, target)
    return Command(verb, target)
