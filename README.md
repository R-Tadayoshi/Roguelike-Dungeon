# Roguelike Dungeon

A turn-based medieval fantasy dungeon crawler for the terminal. Descend through
procedurally generated floors, fight rats, goblins and skeletons, and read the
dungeon's story in the message log as you explore.

```
  ###########                THE ADVENTURER
  #.........#                Attack  6   Defense 1
  #...@.....#######
  #......!........#          IN SIGHT
  #####.###########          g goblin         ██████░░
      #g#
 HP ████████░░░░ 22/30    Depth 2    Level 2    XP 4/40    Kills 3
 ──────────────────────────────────────────────────────────────────
 A goblin shrieks a war-cry and charges!
 The goblin's blade grazes your arm. -3 HP
```

## Requirements

- Python 3.11 or newer
- Windows Terminal (recommended), or any terminal with ANSI color support
- A window of at least **100 x 28** characters

## Running it

```powershell
# from the project folder
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On macOS or Linux, use `python3 -m venv .venv` and `source .venv/bin/activate`.

Run `python main.py --seed 42` to play a repeatable dungeon.

## Controls

| Key                | Action                            |
|--------------------|-----------------------------------|
| WASD / arrow keys  | Move; walk into a monster to attack |
| `g`                | Pick up the item you're standing on |
| `i`                | Open your inventory; press a letter to drink |
| `>` or Enter       | Descend the stairs                |
| `.` or Space       | Wait a turn                       |
| `m`                | Message history (scroll with W/S or arrows) |
| `?`                | Help                              |
| Esc                | Quit (asks to confirm)            |

Map legend: `@` you, `r` giant rat, `g` goblin, `s` skeleton, `!` potion,
`>` stairs, `#` wall, `.` floor.

## How it plays

- The game is turn-based. Monsters act after you do.
- You see only what is in your line of sight. Places you've explored stay on
  the map, dimmed.
- Monsters notice you when you can see them, chase you, and give up if they
  lose your trail.
- Each attack can miss, crit, or be absorbed by armor.
- Kills earn XP. Each level adds max HP and attack, and every other level adds
  defense.
- You recover 1 HP every 8 turns. Potions heal far more.
- Every floor down has more and tougher monsters.

## Project layout

```
main.py         entry point and input loop
game.py         game state, turn order, actions (no terminal code)
map_gen.py      rooms-and-corridors floor generator
fov.py          recursive shadowcasting field of view
ai.py           monster behavior and pathfinding
combat.py       attack rolls and combat narration
entities.py     Player, Monster and Item classes
ui.py           blessed rendering, panels and key mapping
data/
  monsters.py   monster stats, spawn tables and narration
  items.py      item definitions
  rooms.py      room descriptions and per-depth intro text
  combat_text.py  narration for the player's attacks
tests/          logic tests (python -m unittest)
```

## Adding content

Everything you can add is a plain Python dict in `data/`:

- **New monster**: add an entry to `MONSTERS` in `data/monsters.py` with its
  stats, a `spawn` table such as `[(3, 20), (6, 40)]` (from depth 3 at weight
  20, from depth 6 at weight 40), and lists of `notice`, `hit`, `miss` and
  `death` lines.
- **New potion**: add an entry to `ITEMS` in `data/items.py`. Healing is the
  only effect for now.
- **More atmosphere**: add lines to `ROOM_DESCRIPTIONS` or `DEPTH_INTROS` in
  `data/rooms.py`.

Colors are [blessed color names](https://blessed.readthedocs.io/en/latest/colors.html),
for example `"tan"`, `"bold_green"` or `"orchid"`.

## Tests

```
python -m unittest
```
