"""Game state and turn logic. Knows nothing about the terminal; ui.py draws it."""

from __future__ import annotations

import random
from dataclasses import dataclass

from combat import describe_monster_attack, describe_player_attack, resolve_attack
from commands import parse
from data import combat_text
from data.items import ITEMS
from data.monsters import MONSTERS
from data.rooms import DEPTH_INTROS, REST_INTERRUPTED, ROOMS
from entities import Item, Monster, Player
from map_gen import DIRECTIONS, Room, generate_floor

PLAYING = "playing"
DEAD = "dead"
CONFIRM_QUIT = "confirm_quit"

INVENTORY_SIZE = 12
REGEN_INTERVAL = 8  # Turns per point of natural healing.
MAX_REST_TURNS = 60
REST_HEAL_INTERVAL = 2  # While resting, an extra point of healing every this many turns.
WANDERER_CHANCE = 0.04  # Per turn of rest: chance a wandering monster finds you.

EXIT_ORDER = ["north", "east", "south", "west"]

HELP_LINES = [
    "Commands (short forms in brackets):",
    "  go north [n s e w]  move to another room",
    "  attack goblin [a]   'a 2' hits monster #2",
    "  take potion [g]     'take' grabs it all",
    "  drink potion        heal your wounds",
    "  descend [d]         take the stairs down",
    "  look [l]            look around again",
    "  inventory [i]       check your pack",
    "  wait [z]            let a turn pass",
    "  rest                rest until healed",
    "  color on/off        switch colors",
    "  stats  help  quit",
    "Up/Down: earlier commands. PgUp/PgDn: scroll.",
]


@dataclass
class Message:
    text: str
    color: str = "white"


def pick_by_depth(table: dict, depth: int, rng: random.Random) -> str | None:
    """Weighted pick from a {key: {"spawn": [(min_depth, weight), ...]}} table."""
    keys, weights = [], []
    for key, entry in table.items():
        weight = 0
        for min_depth, w in entry["spawn"]:
            if depth >= min_depth:
                weight = w
        if weight > 0:
            keys.append(key)
            weights.append(weight)
    return rng.choices(keys, weights)[0] if keys else None


def with_article(name: str) -> str:
    return f"{'an' if name[0] in 'aeiou' else 'a'} {name}"


def join_words(words: list[str]) -> str:
    if len(words) <= 1:
        return "".join(words)
    return ", ".join(words[:-1]) + " and " + words[-1]


def find_by_name(query: str, things: list):
    """First thing whose name matches `query` ("rat" finds "giant rat", "skel" finds "skeleton")."""
    for q in (query, query.rstrip("s")):
        for thing in things:
            name = thing.name.lower()
            if q in name or any(word.startswith(q) for word in name.split()):
                return thing
    return None


class Game:
    def __init__(self, seed: int | None = None, use_color: bool = True):
        self.rng = random.Random(seed)
        # A display preference, so it survives restarts.
        self.use_color = use_color
        self.new_game()

    def new_game(self) -> None:
        self.depth = 1
        self.turn = 0
        self.messages: list[Message] = []
        self.fresh_from = 0  # Index of the first message produced by the latest command.
        self.player = Player()
        self.mode = PLAYING
        self.running = True
        self.death_cause = ""
        self.log("Welcome, adventurer. Type 'help' to see what you can do.", "bold_gold")
        self.build_floor()

    # -- floor setup -----------------------------------------------------
    def build_floor(self) -> None:
        self.floor = generate_floor(self.rng, self.depth, ROOMS)
        self.populate()
        self.room = self.floor.start
        intro = DEPTH_INTROS[min(self.depth, len(DEPTH_INTROS)) - 1]
        self.log("")
        self.log(f"Depth {self.depth}. {intro}", "gold")
        self.enter_room(self.room)

    def populate(self) -> None:
        max_per_room = min(1 + self.depth // 3, 3)
        for room in self.floor.rooms:
            if room is self.floor.start:
                continue  # A quiet first room gives the player a moment to breathe.
            for _ in range(self.rng.randint(0, max_per_room)):
                room.monsters.append(self.make_monster())
        for room in self.rng.sample(self.floor.rooms, self.rng.randint(2, 3)):
            room.items.append(self.make_item())

    def make_monster(self) -> Monster:
        kind = pick_by_depth(MONSTERS, self.depth, self.rng)
        return Monster(kind, MONSTERS[kind], self.depth)

    def make_item(self) -> Item:
        kind = pick_by_depth(ITEMS, self.depth, self.rng)
        return Item(kind, ITEMS[kind])

    # -- narration -------------------------------------------------------
    def log(self, text: str, color: str = "white") -> None:
        self.messages.append(Message(text, color))

    def exits_text(self) -> str:
        return join_words([d for d in EXIT_ORDER if d in self.room.exits])

    def describe_room(self, room: Room, full: bool, noticed: tuple = ()) -> None:
        """Narrate a room. Monsters in `noticed` just spotted you; the rest are described lurking."""
        self.log(f"== {room.name} ==", "bold_gold")
        if full:
            self.log(room.description, "wheat")
        for monster in room.monsters:
            if monster in noticed:
                self.log(self.rng.choice(monster.template["notice"]), "orange")
            else:
                self.log(monster.template["lurk"], "orange")
        if room.items:
            names = join_words([with_article(item.name) for item in room.items])
            self.log(f"On the floor you see {names}.", "orchid")
        if room.stairs:
            self.log("A stone stairway spirals down into darkness.", "bold_white")
        self.log(f"Exits: {self.exits_text()}.", "gray70")

    def enter_room(self, room: Room) -> None:
        noticed = tuple(m for m in room.monsters if not m.alerted)
        for monster in room.monsters:
            monster.alerted = True
            # Whoever walks in gets the first move.
            monster.arrived_turn = self.turn
        self.describe_room(room, full=not room.visited, noticed=noticed)
        room.visited = True

    # -- input -----------------------------------------------------------
    def submit(self, text: str) -> None:
        """Handle one line typed by the player."""
        text = text.strip()
        if not text:
            return
        self.fresh_from = len(self.messages)
        self.log("")
        self.log(f"> {text}", "bold_cyan")
        answer = text.lower()

        if self.mode == DEAD:
            if answer in ("restart", "r", "new", "yes", "y", "again"):
                self.new_game()
            elif answer in ("quit", "q", "exit", "no", "n"):
                self.running = False
            else:
                self.log("Type 'restart' to descend again, or 'quit' to leave.", "gray70")
            return
        if self.mode == CONFIRM_QUIT:
            if answer in ("yes", "y", "quit", "q"):
                self.running = False
            else:
                self.mode = PLAYING
                self.log("You steel yourself and press on.", "gray70")
            return

        command = parse(text)
        if command is None:
            self.log(f"You're not sure how to '{text}'. Type 'help' for a list of commands.", "gray70")
            return
        handler = getattr(self, f"do_{command.verb}")
        if handler(command.target):
            self.end_turn()

    # -- commands: each returns True if it used up the player's turn ------
    def do_go(self, direction: str) -> bool:
        if not direction:
            self.log(f"Go where? Exits: {self.exits_text()}.", "gray70")
            return False
        if direction not in DIRECTIONS:
            self.log(f"'{direction}' isn't a direction. Exits: {self.exits_text()}.", "gray70")
            return False
        if direction not in self.room.exits:
            self.log(f"There is no way {direction} from here. Exits: {self.exits_text()}.", "gray70")
            return False

        old, new = self.room, self.room.exits[direction]
        followers = [m for m in old.monsters if self.rng.random() < m.template["follow"]]
        if old.monsters:
            self.log(f"You break away and dash {direction}!", "white")
        else:
            self.log(f"You head {direction}.", "gray70")
        self.room = new
        self.enter_room(new)
        for monster in followers:
            old.monsters.remove(monster)
            new.monsters.append(monster)
            monster.arrived_turn = self.turn
            self.log(f"The {monster.name} follows you {direction}!", "orange")
        return True

    def do_attack(self, target: str) -> bool:
        monsters = self.room.monsters
        if not monsters:
            self.log("There is nothing here to fight.", "gray70")
            return False
        if not target:
            monster = monsters[0]
        elif target.isdigit():
            index = int(target) - 1
            monster = monsters[index] if 0 <= index < len(monsters) else None
        else:
            monster = find_by_name(target, monsters)
        if monster is None:
            names = join_words([m.name for m in monsters])
            self.log(f"There is no {target} here. You see: {names}.", "gray70")
            return False

        result = resolve_attack(self.rng, self.player, monster)
        self.log(*describe_player_attack(self.rng, result, monster))
        if result.killed:
            self.kill_monster(monster)
        return True

    def do_take(self, target: str) -> bool:
        items = self.room.items
        if not items:
            self.log("There is nothing here to pick up.", "gray70")
            return False
        if target in ("", "all", "everything"):
            wanted = list(items)
        else:
            item = find_by_name(target, items)
            if item is None:
                self.log(f"There is no {target} here.", "gray70")
                return False
            wanted = [item]
        taken = 0
        for item in wanted:
            if len(self.player.inventory) >= INVENTORY_SIZE:
                self.log("Your pack is full.", "gray70")
                break
            items.remove(item)
            self.player.inventory.append(item)
            self.log(self.rng.choice(item.template["pickup"]), "orchid")
            taken += 1
        return taken > 0

    def do_drink(self, target: str) -> bool:
        potions = [i for i in self.player.inventory if i.template["effect"] == "heal"]
        if not potions:
            self.log("You have nothing to drink.", "gray70")
            return False
        if self.player.hp >= self.player.max_hp:
            self.log("You are already at full health. Better save it.", "gray70")
            return False
        if target and target not in ("potion", "potions"):
            item = find_by_name(target, potions)
            if item is None:
                self.log(f"You don't have a {target}.", "gray70")
                return False
        else:
            # The smallest potion that covers your wounds, or the biggest if none does.
            missing = self.player.max_hp - self.player.hp
            enough = [p for p in potions if p.template["amount"] >= missing]
            if enough:
                item = min(enough, key=lambda p: p.template["amount"])
            else:
                item = max(potions, key=lambda p: p.template["amount"])
        healed = self.player.heal(item.template["amount"])
        self.player.inventory.remove(item)
        self.log(f"{self.rng.choice(item.template['use'])} +{healed} HP", "bold_green")
        return True

    def do_look(self, target: str) -> bool:
        self.describe_room(self.room, full=True)
        return False

    def do_inventory(self, target: str) -> bool:
        inv = self.player.inventory
        if not inv:
            self.log("Your pack is empty.", "gray70")
            return False
        counts: dict[str, int] = {}
        for item in inv:
            counts[item.name] = counts.get(item.name, 0) + 1
        parts = [with_article(n) if c == 1 else f"{c} {n}s" for n, c in counts.items()]
        self.log(f"Your pack holds {join_words(parts)}. ({len(inv)}/{INVENTORY_SIZE})", "orchid")
        return False

    def do_wait(self, target: str) -> bool:
        self.log("You wait, listening to the dungeon breathe.", "gray70")
        return True

    def do_rest(self, target: str) -> bool:
        if self.room.monsters:
            self.log("You can't rest with enemies this close!", "gray70")
            return False
        if self.player.hp >= self.player.max_hp:
            self.log("You are not tired or hurt.", "gray70")
            return False
        start_hp, turns = self.player.hp, 0
        while turns < MAX_REST_TURNS and self.player.hp < self.player.max_hp:
            turns += 1
            if self.rng.random() < WANDERER_CHANCE:
                monster = self.make_monster()
                monster.alerted = True
                monster.arrived_turn = self.turn
                self.room.monsters.append(monster)
                self.log(f"You rest for {turns} turns and recover {self.player.hp - start_hp} HP.", "green")
                self.log(self.rng.choice(REST_INTERRUPTED), "orange")
                self.log(self.rng.choice(monster.template["notice"]), "orange")
                return True
            if turns % REST_HEAL_INTERVAL == 0:
                self.player.heal(1)
            self.end_turn()
        self.log(f"You rest for {turns} turns and recover {self.player.hp - start_hp} HP.", "green")
        return False

    def do_descend(self, target: str) -> bool:
        if not self.room.stairs:
            self.log("There are no stairs here.", "gray70")
            return False
        if self.room.monsters:
            self.log("You slip past your foes and hurry down the stairs!", "white")
        self.depth += 1
        self.log("You descend the winding stairs. The air grows colder.", "gray70")
        self.build_floor()
        return False  # A fresh floor: nothing gets a parting blow.

    def do_stats(self, target: str) -> bool:
        p = self.player
        self.log(
            f"Level {p.level} ({p.xp}/{p.xp_to_next} XP). HP {p.hp}/{p.max_hp}, "
            f"attack {p.attack}, defense {p.defense}. Depth {self.depth}, {p.kills} kills, turn {self.turn}.",
            "wheat",
        )
        return False

    def do_color(self, target: str) -> bool:
        if target in ("on", "yes"):
            self.use_color = True
        elif target in ("off", "no", "none"):
            self.use_color = False
        elif target == "":
            self.use_color = not self.use_color
        else:
            self.log("Type 'color on' or 'color off'.", "gray70")
            return False
        self.log(f"Colors are now {'on' if self.use_color else 'off'}.", "gray70")
        return False

    def do_help(self, target: str) -> bool:
        for line in HELP_LINES:
            self.log(line, "gray70")
        return False

    def do_quit(self, target: str) -> bool:
        self.mode = CONFIRM_QUIT
        self.log("Abandon this run? (yes/no)", "bold_white")
        return False

    # -- combat and turn flow --------------------------------------------
    def kill_monster(self, monster: Monster) -> None:
        self.room.monsters.remove(monster)
        self.player.kills += 1
        self.player.kills_by_kind[monster.name] = self.player.kills_by_kind.get(monster.name, 0) + 1
        self.log(self.rng.choice(monster.template["death"]), "gold")
        if self.rng.random() < monster.template.get("drop", 0):
            item = self.make_item()
            self.room.items.append(item)
            self.log(f"The {monster.name} drops {with_article(item.name)}.", "orchid")
        if self.player.gain_xp(monster.xp):
            self.log(combat_text.LEVEL_UP.format(level=self.player.level), "bold_cyan")

    def end_turn(self) -> None:
        """After the player acts, every monster in the room that is ready attacks."""
        for monster in list(self.room.monsters):
            if self.mode == DEAD:
                break
            if monster.arrived_turn != self.turn:
                self.monster_attack(monster)
        self.turn += 1
        if self.mode != DEAD and self.turn % REGEN_INTERVAL == 0:
            self.player.heal(1)

    def monster_attack(self, monster: Monster) -> None:
        result = resolve_attack(self.rng, monster, self.player)
        self.log(*describe_monster_attack(self.rng, result, monster))
        if result.killed:
            self.death_cause = f"slain by {with_article(monster.name)}"
            self.log(combat_text.PLAYER_DEATH, "bold_red")
            self.log("Type 'restart' to descend again, or 'quit' to leave.", "bold_gold")
            self.mode = DEAD
