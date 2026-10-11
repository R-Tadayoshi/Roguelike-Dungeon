"""Logic tests that run without a terminal: python -m unittest"""

import random
import unittest

import ai
from combat import resolve_attack
from data.items import ITEMS
from data.monsters import MONSTERS
from data.rooms import ROOM_DESCRIPTIONS
from entities import Item, Monster
from game import DEAD, INVENTORY, PLAYING, Game, pick_by_depth
from map_gen import MAX_ROOMS, STAIRS, generate_floor


class MapGenTests(unittest.TestCase):
    def test_every_floor_tile_reachable_from_start(self):
        for seed in range(50):
            gm = generate_floor(random.Random(seed))
            dist = ai.distance_map(gm, gm.start)
            for y in range(gm.height):
                for x in range(gm.width):
                    if gm.is_walkable(x, y):
                        self.assertLess(dist[y][x], ai.UNREACHABLE, f"seed {seed}: ({x},{y}) unreachable")

    def test_stairs_placed_away_from_start(self):
        for seed in range(50):
            gm = generate_floor(random.Random(seed))
            self.assertEqual(gm.tile(*gm.stairs), STAIRS)
            self.assertNotEqual(gm.start, gm.stairs)

    def test_enough_room_descriptions(self):
        self.assertGreaterEqual(len(ROOM_DESCRIPTIONS), MAX_ROOMS)


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(seed=1234)
        self.game.monsters.clear()

    def place_monster(self, kind="goblin", dx=1, dy=0):
        p = self.game.player
        # Make sure the target tile is floor so the test does not depend on the map layout.
        self.game.game_map.tiles[p.y + dy][p.x + dx] = "."
        m = Monster(p.x + dx, p.y + dy, kind, MONSTERS[kind], depth=1)
        self.game.monsters.append(m)
        return m

    def test_player_starts_in_visible_room(self):
        p = self.game.player
        self.assertTrue(self.game.game_map.visible[p.y][p.x])
        self.assertTrue(self.game.game_map.room_at(*p.pos).visited)

    def test_bump_attack_damages_and_kills(self):
        m = self.place_monster("rat")
        m.hp = 1
        self.game.player.attack = 50
        for _ in range(20):  # Retry past the occasional miss.
            if m not in self.game.monsters:
                break
            self.game.handle(("move", 1, 0))
        self.assertNotIn(m, self.game.monsters)
        self.assertEqual(self.game.player.kills, 1)
        self.assertGreater(self.game.player.xp, 0)

    def test_attack_never_negative_damage(self):
        rng = random.Random(0)
        m = Monster(0, 0, "skeleton", MONSTERS["skeleton"], depth=1)
        m.defense = 100
        for _ in range(100):
            result = resolve_attack(rng, self.game.player, m)
            self.assertGreaterEqual(result.damage, 0)
        self.assertEqual(m.hp, m.max_hp)

    def test_monster_chases_and_attacks(self):
        m = self.place_monster("goblin", dx=1)
        m.attack = 0  # Harmless, we only care that it acts.
        self.game.update_fov()
        self.game.handle(("wait",))
        self.assertTrue(m.alerted)
        self.assertTrue(any("goblin" in msg.text.lower() for msg in self.game.messages))

    def test_player_death_and_restart(self):
        m = self.place_monster("goblin")
        m.attack = 999
        self.game.player.hp = 1
        self.game.update_fov()
        for _ in range(50):
            if self.game.mode == DEAD:
                break
            self.game.handle(("wait",))
        self.assertEqual(self.game.mode, DEAD)
        self.assertIn("goblin", self.game.death_cause)
        self.game.handle(("restart",))
        self.assertEqual(self.game.mode, PLAYING)
        self.assertEqual(self.game.depth, 1)
        self.assertEqual(self.game.player.hp, self.game.player.max_hp)

    def test_pick_up_and_drink_potion(self):
        p = self.game.player
        self.game.items.append(Item(p.x, p.y, "healing_potion", ITEMS["healing_potion"]))
        self.game.handle(("pickup",))
        self.assertEqual(len(p.inventory), 1)
        p.hp = 5
        self.game.handle(("open", INVENTORY))
        self.game.handle(("use", 0))
        self.assertEqual(p.inventory, [])
        self.assertGreater(p.hp, 5)
        self.assertEqual(self.game.mode, PLAYING)

    def test_potion_not_wasted_at_full_health(self):
        p = self.game.player
        p.inventory.append(Item(0, 0, "healing_potion", ITEMS["healing_potion"]))
        self.game.handle(("open", INVENTORY))
        self.game.handle(("use", 0))
        self.assertEqual(len(p.inventory), 1)

    def test_descend_only_on_stairs(self):
        self.game.handle(("descend",))
        self.assertEqual(self.game.depth, 1)
        self.game.player.x, self.game.player.y = self.game.game_map.stairs
        self.game.handle(("descend",))
        self.assertEqual(self.game.depth, 2)
        self.assertEqual(self.game.player.pos, self.game.game_map.start)

    def test_spawn_tables_respect_depth(self):
        rng = random.Random(0)
        picks = {pick_by_depth(MONSTERS, 1, rng) for _ in range(500)}
        self.assertNotIn("skeleton", picks)
        picks = {pick_by_depth(ITEMS, 1, rng) for _ in range(500)}
        self.assertEqual(picks, {"healing_potion"})


if __name__ == "__main__":
    unittest.main()
