"""Narration for the player's attacks. {name} is the monster's name."""

PLAYER_HIT = [
    "You slash the {name}.",
    "Your sword bites into the {name}.",
    "You strike the {name} squarely.",
    "You drive your blade into the {name}.",
]

PLAYER_CRIT = [
    "You land a crushing blow on the {name}!",
    "A perfect strike! Your sword cleaves the {name}!",
]

PLAYER_MISS = [
    "You swing at the {name} and miss.",
    "The {name} slips past your blade.",
]

PLAYER_GLANCE = [
    "Your blow glances off the {name} harmlessly.",
]

# Monster attacks that do no damage after armor.
ARMOR_BLOCK = [
    "The {name}'s attack glances off your armor.",
]

PLAYER_DEATH = "You collapse onto the cold stone. Darkness takes you..."

LEVEL_UP = "You feel stronger! You are now level {level}."
