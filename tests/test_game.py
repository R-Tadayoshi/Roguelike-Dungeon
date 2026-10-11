"""Logic tests that run without a terminal: python -m unittest"""

import random
import unittest

from combat import resolve_attack
from commands import Command, parse
from data.items import ITEMS
from data.monsters import MONSTERS
from data.rooms import ROOMS
from entities import Item, Monster
from game import CONFIRM_QUIT, DEAD, PLAYING, Game, pick_by_depth
from map_gen import GRID_HEIGHT, GRID_WIDTH, OPPOSITE, distances_from, generate_floor, room_count


class ParserTests(unittest.TestCase):
    def test_directions_and_go(self):
        self.assertEqual(parse("n"), Command("go", "north"))
        self.assertEqual(parse("go east"), Command("go", "east"))
        self.assertEqual(parse("walk to the west"), Command("go", "west"))
        self.assertEqual(parse("go down"), Command("descend"))

    def test_verbs_targets_and_filler(self):
        self.assertEqual(parse("attack the goblin"), Command("attack", "goblin"))
        self.assertEqual(parse("a rat"), Command("attack", "rat"))
        self.assertEqual(parse("a 2"), Command("attack", "2"))
        self.assertEqual(parse("pick up a potion"), Command("take", "potion"))
        self.assertEqual(parse("Drink Greater Potion"), Command("drink", "greater potion"))
        self.assertEqual(parse("i"), Command("inventory"))

    def test_unknown(self):
        self.assertIsNone(parse("dance wildly"))
        self.assertIsNone(parse(""))


class MapGenTests(unittest.TestCase):
    def test_floors_are_connected_with_consistent_exits(self):
        for seed in range(100):
            depth = seed % 12 + 1
            floor = generate_floor(random.Random(seed), depth, ROOMS)
            self.assertEqual(len(floor.rooms), room_count(depth))
            self.assertEqual(len(distances_from(floor.start)), len(floor.rooms))
            for room in floor.rooms:
                self.assertTrue(0 <= room.gx < GRID_WIDTH and 0 <= room.gy < GRID_HEIGHT)
                for direction, other in room.exits.items():
                    self.assertIs(other.exits[OPPOSITE[direction]], room)

    def test_one_staircase_away_from_start(self):
        for seed in range(50):
            floor = generate_floor(random.Random(seed), 1, ROOMS)
            self.assertEqual(sum(r.stairs for r in floor.rooms), 1)
            self.assertFalse(floor.start.stairs)

    def test_enough_room_texts_for_largest_floor(self):
        self.assertGreaterEqual(len(ROOMS), room_count(100))


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(seed=1234)
        for room in self.game.floor.rooms:
            room.monsters.clear()

    def add_monster(self, kind="goblin"):
        monster = Monster(kind, MONSTERS[kind], depth=1)
        monster.alerted = True
        self.game.room.monsters.append(monster)
        return monster

    def last_texts(self, n=10):
        return " ".join(m.text for m in self.game.messages[-n:])

    def test_start_room_is_described(self):
        self.assertTrue(self.game.room.visited)
        self.assertIn(self.game.room.description, self.last_texts(20))

    def test_moving_between_rooms(self):
        direction, target = next(iter(self.game.room.exits.items()))
        self.game.submit(direction[0])
        self.assertIs(self.game.room, target)
        self.assertTrue(target.visited)
        self.assertEqual(self.game.turn, 1)

    def test_blocked_direction_costs_no_turn(self):
        blocked = next(d for d in ("north", "south", "east", "west") if d not in self.game.room.exits)
        start = self.game.room
        self.game.submit(f"go {blocked}")
        self.assertIs(self.game.room, start)
        self.assertEqual(self.game.turn, 0)

    def test_attack_kills_and_awards_xp(self):
        monster = self.add_monster("rat")
        monster.hp = 1
        self.game.player.attack = 50
        for _ in range(20):  # Retry past the occasional miss.
            if monster not in self.game.room.monsters:
                break
            self.game.submit("attack rat")
        self.assertNotIn(monster, self.game.room.monsters)
        self.assertEqual(self.game.player.kills, 1)
        self.assertGreater(self.game.player.xp, 0)

    def test_attack_by_number(self):
        self.add_monster("rat")
        goblin = self.add_monster("goblin")
        goblin.hp = 1
        self.game.player.attack = 50
        for _ in range(20):
            if goblin not in self.game.room.monsters:
                break
            self.game.submit("a 2")
        self.assertNotIn(goblin, self.game.room.monsters)

    def test_unknown_target_costs_no_turn(self):
        self.add_monster("rat")
        self.game.submit("attack dragon")
        self.assertEqual(self.game.turn, 0)
        self.assertIn("no dragon", self.last_texts())

    def test_attack_never_negative_damage(self):
        rng = random.Random(0)
        monster = Monster("skeleton", MONSTERS["skeleton"], depth=1)
        monster.defense = 100
        for _ in range(100):
            self.assertGreaterEqual(resolve_attack(rng, self.game.player, monster).damage, 0)
        self.assertEqual(monster.hp, monster.max_hp)

    def test_monster_entering_with_player_waits_a_turn(self):
        # Walk into a room with a monster: it notices you but doesn't strike until your next action.
        direction, target = next(iter(self.game.room.exits.items()))
        monster = Monster("goblin", MONSTERS["goblin"], depth=1)
        monster.attack = 999
        target.monsters.append(monster)
        self.game.submit(direction)
        self.assertEqual(self.game.mode, PLAYING)
        self.assertTrue(monster.alerted)
        self.game.submit("wait")
        texts = [m.text for m in self.game.messages[-4:]]
        # With 999 attack its first strike is fatal, unless it rolls a miss.
        self.assertTrue(self.game.mode == DEAD or any(t in MONSTERS["goblin"]["miss"] for t in texts))

    def test_followers_chase_into_next_room(self):
        monster = self.add_monster("goblin")
        monster.template = dict(monster.template, follow=1.0)
        direction, target = next(iter(self.game.room.exits.items()))
        self.game.submit(direction)
        self.assertIn(monster, target.monsters)
        self.assertIn("follows you", self.last_texts())

    def test_death_and_restart(self):
        monster = self.add_monster("goblin")
        monster.attack = 999
        self.game.player.hp = 1
        for _ in range(50):
            if self.game.mode == DEAD:
                break
            self.game.submit("wait")
        self.assertEqual(self.game.mode, DEAD)
        self.assertIn("goblin", self.game.death_cause)
        self.game.submit("restart")
        self.assertEqual(self.game.mode, PLAYING)
        self.assertEqual(self.game.depth, 1)
        self.assertEqual(self.game.player.hp, self.game.player.max_hp)

    def test_take_and_drink(self):
        p = self.game.player
        self.game.room.items[:] = [Item("healing_potion", ITEMS["healing_potion"])]
        self.game.submit("take potion")
        self.assertEqual(len(p.inventory), 1)
        self.game.submit("drink")
        self.assertEqual(len(p.inventory), 1, "potion should not be wasted at full health")
        p.hp = 5
        self.game.submit("drink potion")
        self.assertEqual(p.inventory, [])
        self.assertGreater(p.hp, 5)

    def test_drink_picks_smallest_sufficient_potion(self):
        p = self.game.player
        p.inventory = [Item("greater_healing_potion", ITEMS["greater_healing_potion"]),
                       Item("healing_potion", ITEMS["healing_potion"])]
        p.hp = p.max_hp - 5
        self.game.submit("drink")
        self.assertEqual([i.kind for i in p.inventory], ["greater_healing_potion"])

    def test_rest_heals_when_safe_and_refuses_in_combat(self):
        p = self.game.player
        p.hp = 5
        self.game.submit("rest")
        self.assertGreater(p.hp, 5)
        self.game.room.monsters.clear()
        self.add_monster("rat")
        hp = p.hp
        turn = self.game.turn
        self.game.submit("rest")
        self.assertEqual((p.hp, self.game.turn), (hp, turn))

    def test_descend_only_on_stairs(self):
        self.game.submit("descend")
        self.assertEqual(self.game.depth, 1)
        self.game.room = self.game.floor.stairs_room
        self.game.submit("d")
        self.assertEqual(self.game.depth, 2)
        self.assertIs(self.game.room, self.game.floor.start)

    def test_quit_asks_for_confirmation(self):
        self.game.submit("quit")
        self.assertEqual(self.game.mode, CONFIRM_QUIT)
        self.game.submit("no")
        self.assertTrue(self.game.running)
        self.assertEqual(self.game.mode, PLAYING)
        self.game.submit("q")
        self.game.submit("yes")
        self.assertFalse(self.game.running)

    def test_color_command_toggles_without_using_a_turn(self):
        self.assertTrue(self.game.use_color)
        self.game.submit("color off")
        self.assertFalse(self.game.use_color)
        self.game.submit("colour")
        self.assertTrue(self.game.use_color)
        self.assertEqual(self.game.turn, 0)

    def test_color_preference_survives_restart(self):
        game = Game(seed=1, use_color=False)
        game.new_game()
        self.assertFalse(game.use_color)

    def test_unknown_command(self):
        self.game.submit("juggle")
        self.assertIn("help", self.last_texts(2))
        self.assertEqual(self.game.turn, 0)

    def test_spawn_tables_respect_depth(self):
        rng = random.Random(0)
        self.assertNotIn("skeleton", {pick_by_depth(MONSTERS, 1, rng) for _ in range(500)})
        self.assertEqual({pick_by_depth(ITEMS, 1, rng) for _ in range(500)}, {"healing_potion"})


if __name__ == "__main__":
    unittest.main()
