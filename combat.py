"""Attack resolution and combat narration."""

from __future__ import annotations

import random
from dataclasses import dataclass

from data import combat_text
from entities import Actor, Monster

MISS_CHANCE = 0.12
CRIT_CHANCE = 0.08


@dataclass
class AttackResult:
    hit: bool
    damage: int = 0
    crit: bool = False
    killed: bool = False


def resolve_attack(rng: random.Random, attacker: Actor, defender: Actor) -> AttackResult:
    """Roll one attack and apply its damage to the defender."""
    if rng.random() < MISS_CHANCE:
        return AttackResult(hit=False)
    crit = rng.random() < CRIT_CHANCE
    raw = attacker.attack + rng.randint(-1, 2)
    if crit:
        raw = raw * 3 // 2 + 1
    damage = max(0, raw - defender.defense)
    defender.hp = max(0, defender.hp - damage)
    return AttackResult(hit=True, damage=damage, crit=crit, killed=not defender.is_alive)


def describe_player_attack(rng: random.Random, result: AttackResult, monster: Monster) -> tuple[str, str]:
    """Return (text, color) narrating the player's attack on a monster."""
    if not result.hit:
        return rng.choice(combat_text.PLAYER_MISS).format(name=monster.name), "gray70"
    if result.damage == 0:
        return rng.choice(combat_text.PLAYER_GLANCE).format(name=monster.name), "gray70"
    pool = combat_text.PLAYER_CRIT if result.crit else combat_text.PLAYER_HIT
    text = f"{rng.choice(pool).format(name=monster.name)} -{result.damage} HP"
    return text, "bold_yellow" if result.crit else "white"


def describe_monster_attack(rng: random.Random, result: AttackResult, monster: Monster) -> tuple[str, str]:
    """Return (text, color) narrating a monster's attack on the player."""
    if not result.hit:
        return rng.choice(monster.template["miss"]), "gray70"
    if result.damage == 0:
        return rng.choice(combat_text.ARMOR_BLOCK).format(name=monster.name), "gray70"
    text = f"{rng.choice(monster.template['hit'])} -{result.damage} HP"
    return text, "bold_red" if result.crit else "red"
