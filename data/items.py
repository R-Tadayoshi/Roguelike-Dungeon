"""Item definitions.

To add an item, add an entry here. Fields:
  name, char, color   how it looks
  effect, amount      what using it does (currently "heal")
  spawn               list of (min_depth, weight), same rules as monsters
  pickup / use        narration; one line is picked at random
"""

ITEMS = {
    "healing_potion": {
        "name": "healing potion",
        "char": "!",
        "color": "bold_red",
        "effect": "heal",
        "amount": 12,
        "spawn": [(1, 100), (5, 70)],
        "pickup": [
            "You pick up a healing potion. The red liquid glows faintly.",
            "You tuck a small vial of healing draught into your pack.",
        ],
        "use": [
            "You drink the healing potion. Warmth spreads through your chest.",
            "You gulp down the potion. It tastes of copper and summer berries.",
        ],
    },
    "greater_healing_potion": {
        "name": "greater healing potion",
        "char": "!",
        "color": "bold_magenta",
        "effect": "heal",
        "amount": 25,
        "spawn": [(3, 25), (5, 45)],
        "pickup": [
            "You pick up a greater healing potion. It pulses with violet light.",
        ],
        "use": [
            "You drain the greater healing potion. Your wounds knit closed before your eyes.",
        ],
    },
}
