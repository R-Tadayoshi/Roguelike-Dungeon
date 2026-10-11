"""Monster definitions.

To add a monster, add an entry here. Fields:
  name, char, color       how it shows in the sidebar (color is any blessed color name, e.g. "tan")
  hp, attack, defense     base stats at depth 1 (scaled up on deeper floors)
  xp                      experience awarded for the kill
  follow                  chance (0-1) it chases you into the next room when you leave mid-fight
  drop                    chance (0-1) it leaves a healing potion behind when it dies
  spawn                   list of (min_depth, weight): the last entry whose min_depth <= depth is used
  lurk                    how it's described when you look around a room it's in
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
        "follow": 0.5,
        "drop": 0.05,
        "spawn": [(1, 60), (3, 35), (6, 15)],
        "lurk": "A giant rat sniffs the air, whiskers twitching.",
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
        "attack": 4,
        "defense": 1,
        "xp": 8,
        "follow": 0.8,
        "drop": 0.2,
        "spawn": [(1, 30), (3, 50), (6, 40)],
        "lurk": "A goblin glares at you, notched blade drawn.",
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
        "hp": 14,
        "attack": 6,
        "defense": 2,
        "xp": 15,
        "follow": 0.6,
        "drop": 0.25,
        "spawn": [(2, 10), (4, 35), (6, 55)],
        "lurk": "A skeleton sways in place, its bones creaking.",
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
