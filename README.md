# Roguelike Dungeon

A medieval fantasy text adventure with roguelike bones. You type commands to explore a
dungeon of randomly generated rooms, fight rats, goblins and skeletons, and go as deep
as you dare. Every floor is different, and when you die the run is over.

```
 HP ███████░░░░░ 17/30   Depth 3   Level 1   XP 9/18   Kills 3
──────────────────────────────────────────────────────────────────────────────
 > east                                         │ ATTACK 5   DEFENSE 1
 You head east.                                 │ MAP OF DEPTH 3
 == Flooded Cistern ==                          │ [ ]-[@]-[?]
 Cold water drips from the vaulted ceiling into │      |
 a shallow, stagnant pool that soaks your       │     [?]
 boots.                                         │
 A goblin spots you and draws a notched blade.  │ HERE
 Exits: east, south and west.                   │ 1 goblin          ██████░░
                                                │
 > attack goblin                                │ PACK (0/12)
 You strike the goblin squarely. -4 HP          │ Empty.
 The goblin's blade grazes your arm. -6 HP      │
──────────────────────────────────────────────────────────────────────────────
 > _
```

## Requirements

- Python 3.11 or newer
- Windows Terminal (recommended), or any terminal with ANSI color support
- A window of at least **80 x 24** characters

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

## Commands

Type a command and press Enter. Short forms are in brackets.

| Command                       | What it does |
|-------------------------------|--------------|
| `go north` [`n` `s` `e` `w`]  | Move to the next room |
| `attack goblin` [`a`]         | Attack a monster. `a` alone hits the first one; `a 2` hits the second one listed |
| `take potion` [`g`]           | Pick something up. `take` alone grabs everything |
| `drink potion`                | Drink a healing potion. Without a name, it picks the smallest one that heals you fully |
| `descend` [`d`]               | Take the stairs down to the next floor |
| `look` [`l`]                  | Describe the room again |
| `inventory` [`i`]             | List what you're carrying |
| `wait` [`z`]                  | Let a turn pass |
| `rest`                        | Rest until healed. Only works with no enemies around, and something may find you |
| `stats`, `help`, `quit`       | Show your stats, list commands, quit (asks to confirm) |

The parser ignores filler words, so "attack the goblin" and "pick up a potion" work.
Partial names work too: `a skel` attacks the skeleton.

Keys: **Up/Down** recalls earlier commands, **PgUp/PgDn** scrolls back through the
story, and **Esc** clears the line.

## How it plays

- The game is turn-based. Every command that takes time (moving, attacking, picking
  up, drinking, waiting) lets the monsters in your room act afterwards. `look`,
  `inventory`, `stats` and `help` are free.
- When you walk into a room, you get the first move.
- Leaving a fight is allowed, but monsters may follow you into the next room.
  Goblins are the most persistent. Taking the stairs always gets you away.
- Each attack can miss, crit, or be absorbed by armor.
- Kills earn XP. Each level adds max HP and attack, and every other level adds
  defense. Monsters sometimes drop potions.
- You recover 1 HP every 8 turns. `rest` heals faster but can attract wandering
  monsters.
- Monsters get stronger on every floor, faster than you can level up, so eventually
  the dungeon wins. How deep can you get?

The sidebar map shows the rooms you've visited (`@` you, `>` stairs, `!` an item
left behind) and the doorways leading out of them (`?` rooms you haven't entered yet).

## Project layout

```
main.py         entry point and input loop
game.py         game state, commands, turn order (no terminal code)
commands.py     text parser: "attack the goblin" -> attack / goblin
map_gen.py      floors as networks of rooms on a small grid
combat.py       attack rolls and combat narration
entities.py     Player, Monster and Item classes
ui.py           blessed rendering, sidebar map and the command line
data/
  monsters.py   monster stats, spawn tables and narration
  items.py      item definitions
  rooms.py      room names, descriptions and per-depth intro text
  combat_text.py  narration for the player's attacks
tests/          logic tests (python -m unittest)
```

## Adding content

Everything you can add is a plain Python dict in `data/`:

- **New monster**: add an entry to `MONSTERS` in `data/monsters.py` with its stats,
  how likely it is to follow you (`follow`) and drop a potion (`drop`), a `spawn`
  table such as `[(3, 20), (6, 40)]` (from depth 3 at weight 20, from depth 6 at
  weight 40), and its narration lines.
- **New potion**: add an entry to `ITEMS` in `data/items.py`. Healing is the only
  effect for now.
- **New rooms**: add a `{"name": ..., "description": ...}` entry to `ROOMS` in
  `data/rooms.py`. More rooms means fewer repeats.
- **New command words**: add synonyms to `VERBS` in `commands.py`.

Colors are [blessed color names](https://blessed.readthedocs.io/en/latest/colors.html),
for example `"tan"`, `"bold_green"` or `"orchid"`.

## Tests

```
python -m unittest
```
