"""The player, monsters and items."""

from __future__ import annotations


class Actor:
    """Anything that has hit points and can fight."""

    def __init__(self, name: str, hp: int, attack: int, defense: int):
        self.name = name
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
    def __init__(self):
        super().__init__("you", hp=30, attack=5, defense=1)
        self.level = 1
        self.xp = 0
        self.kills = 0
        self.kills_by_kind: dict[str, int] = {}
        self.inventory: list[Item] = []

    @property
    def xp_to_next(self) -> int:
        # Grows faster than monster XP does, so each level takes longer than the last.
        return 15 * self.level + 3 * self.level * self.level

    def gain_xp(self, amount: int) -> int:
        """Add experience; return how many levels were gained."""
        self.xp += amount
        gained = 0
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            gained += 1
            self.max_hp += 7
            self.hp = min(self.max_hp, self.hp + 7)
            self.attack += 1
            if self.level % 2 == 0:
                self.defense += 1
        return gained


class Monster(Actor):
    """A monster built from a template in data/monsters.py, scaled to the dungeon depth."""

    def __init__(self, kind: str, template: dict, depth: int):
        # Monsters toughen steadily with depth so the player can't simply out-level the dungeon.
        hp = round(template["hp"] * (1 + 0.2 * (depth - 1)))
        attack = template["attack"] + (depth - 1) * 2 // 3
        defense = template["defense"] + (depth - 1) // 3
        super().__init__(template["name"], hp, attack, defense)
        self.kind = kind
        self.template = template
        self.char = template["char"]
        self.color = template["color"]
        self.xp = template["xp"] + depth - 1
        self.alerted = False
        # The turn it walked into the player's room; it can't attack until the next turn.
        self.arrived_turn = -1


class Item:
    """An item built from a template in data/items.py."""

    def __init__(self, kind: str, template: dict):
        self.kind = kind
        self.template = template
        self.name = template["name"]
        self.char = template["char"]
        self.color = template["color"]
