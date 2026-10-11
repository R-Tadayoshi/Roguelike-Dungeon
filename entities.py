"""Things that live on the map: the player, monsters and items."""

from __future__ import annotations


class Entity:
    def __init__(self, x: int, y: int, char: str, color: str, name: str):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name

    @property
    def pos(self) -> tuple[int, int]:
        return (self.x, self.y)


class Actor(Entity):
    """Anything that has hit points and can fight."""

    def __init__(self, x, y, char, color, name, hp: int, attack: int, defense: int):
        super().__init__(x, y, char, color, name)
        self.max_hp = hp
        self.hp = hp
        self.attack = attack
        self.defense = defense

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def heal(self, amount: int) -> int:
        """Restore up to `amount` HP and return how much was actually healed."""
        healed = min(amount, self.max_hp - self.hp)
        self.hp += healed
        return healed


class Player(Actor):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, "@", "bold_yellow", "you", hp=30, attack=5, defense=1)
        self.level = 1
        self.xp = 0
        self.kills = 0
        self.inventory: list[Item] = []

    @property
    def xp_to_next(self) -> int:
        return self.level * 20

    def gain_xp(self, amount: int) -> int:
        """Add experience; return how many levels were gained."""
        self.xp += amount
        gained = 0
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            gained += 1
            self.max_hp += 8
            self.hp = min(self.max_hp, self.hp + 8)
            self.attack += 1
            if self.level % 2 == 0:
                self.defense += 1
        return gained


class Monster(Actor):
    """A monster built from a template in data/monsters.py, scaled to the dungeon depth."""

    def __init__(self, x: int, y: int, kind: str, template: dict, depth: int):
        hp = round(template["hp"] * (1 + 0.12 * (depth - 1)))
        attack = template["attack"] + depth // 3
        defense = template["defense"] + depth // 5
        super().__init__(x, y, template["char"], template["color"], template["name"], hp, attack, defense)
        self.kind = kind
        self.template = template
        self.ai = template.get("ai", "chase")
        self.xp = template["xp"] + depth - 1
        self.alerted = False
        self.last_seen: tuple[int, int] | None = None


class Item(Entity):
    """An item built from a template in data/items.py."""

    def __init__(self, x: int, y: int, kind: str, template: dict):
        super().__init__(x, y, template["char"], template["color"], template["name"])
        self.kind = kind
        self.template = template
