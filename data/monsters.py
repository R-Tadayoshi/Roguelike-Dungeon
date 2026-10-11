"""Monster definitions.

To add a monster, add an entry here. Fields:
  name, char, color       how it looks (color is any blessed color name, e.g. "tan", "bold_red")
  hp, attack, defense     base stats at depth 1 (scaled up on deeper floors)
  xp                      experience awarded for the kill
  ai                      "chase" (beeline for the player) or "erratic" (chases, but sometimes skitters randomly)
  spawn                   list of (min_depth, weight): the last entry whose min_depth <= depth is used
  notice / hit / miss / death   narration; one line is picked at random each time
"""

MONSTERS = {
    "rat": {
        "name": "giant rat",
        "char": "r",
        "color": "tan",
        "hp": 6,
        "attack": 3,
        "defense": 0,
        "xp": 3,
        "ai": "erratic",
        "spawn": [(1, 60), (3, 35), (6, 15)],
        "notice": [
            "A giant rat squeaks and scurries toward you!",
            "Red eyes glint in the dark. A giant rat bares its teeth.",
        ],
        "hit": [
            "The rat's teeth sink into your ankle.",
            "The rat bites at your leg.",
            "The rat claws its way up your boot and draws blood.",
        ],
        "miss": [
            "The rat snaps at you, catching only air.",
            "The rat lunges and misses.",
        ],
        "death": [
            "The rat squeals once and goes still.",
            "The giant rat collapses in a matted heap.",
        ],
    },
    "goblin": {
        "name": "goblin",
        "char": "g",
        "color": "bold_green",
        "hp": 10,
        "attack": 5,
        "defense": 1,
        "xp": 8,
        "ai": "chase",
        "spawn": [(1, 30), (3, 50), (6, 40)],
        "notice": [
            "A goblin shrieks a war-cry and charges!",
            "A goblin spots you and draws a notched blade.",
        ],
        "hit": [
            "The goblin's blade grazes your arm.",
            "The goblin stabs you in the side.",
            "The goblin cackles as its knife finds a gap in your armor.",
        ],
        "miss": [
            "The goblin's wild swing goes wide.",
            "You sidestep the goblin's clumsy thrust.",
        ],
        "death": [
            "The goblin gurgles and crumples to the floor.",
            "The goblin falls, its blade clattering on the stones.",
        ],
    },
    "skeleton": {
        "name": "skeleton",
        "char": "s",
        "color": "bold_white",
        "hp": 16,
        "attack": 7,
        "defense": 3,
        "xp": 15,
        "ai": "chase",
        "spawn": [(2, 10), (4, 35), (6, 55)],
        "notice": [
            "Bones rattle as a skeleton lurches to life!",
            "A skeleton turns its empty sockets toward you.",
        ],
        "hit": [
            "The skeleton's rusted sword bites into your shoulder.",
            "Bony fingers rake across your face.",
            "The skeleton bashes you with a cracked shield.",
        ],
        "miss": [
            "The skeleton's blade scrapes harmlessly off the wall.",
            "You duck under the skeleton's creaking swing.",
        ],
        "death": [
            "The skeleton shatters into a pile of dry bones.",
            "The skeleton's skull rolls away as the rest collapses.",
        ],
    },
}
