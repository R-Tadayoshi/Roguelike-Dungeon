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
