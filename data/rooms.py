"""Atmospheric flavor text.

ROOMS: each room on a floor gets one name and description. The description is
shown the first time you enter, and again whenever you type "look". Keep at
least as many entries as the largest floor (map_gen.room_count) so a floor
never repeats itself.

DEPTH_INTROS: shown on arriving at a depth. Depths past the end of the list
reuse the last line.
"""

ROOMS = [
    {"name": "Flooded Cistern",
     "description": "Cold water drips from the vaulted ceiling into a shallow, stagnant pool that soaks your boots."},
    {"name": "Old Guardroom",
     "description": "Rusted manacles hang from the walls. Someone scratched tally marks beside them, hundreds of them."},
    {"name": "Broken Chapel",
     "description": "A toppled altar lies in pieces. The air still smells faintly of incense and ash."},
    {"name": "Webbed Hall",
     "description": "Cobwebs thick as curtains drape every corner. Something large spun these."},
    {"name": "Bone Pit",
     "description": "The floor is littered with gnawed bones. Most of them are small. Most of them."},
    {"name": "Tapestry Gallery",
     "description": "A faded tapestry shows a knight slaying a dragon. Someone has slashed out the knight's face."},
    {"name": "Cellar",
     "description": "Old barrels line one wall, their staves split and their contents long since spoiled."},
    {"name": "Sun Mosaic Chamber",
     "description": "A cracked mosaic of a sun covers the floor. It is the only warm color you have seen in hours."},
    {"name": "Sooty Passage",
     "description": "Burnt-out torches sit in iron sconces. The soot above them is fresh."},
    {"name": "Ruined Library",
     "description": "This was a library once. Mouldering pages crunch underfoot like dead leaves."},
    {"name": "Sentinel's Alcove",
     "description": "An empty suit of armor stands in the corner. You could swear its helm just turned to follow you."},
    {"name": "Glowing Grotto",
     "description": "Moss grows thick and green here, glowing with a faint, sickly light."},
    {"name": "Collapsed Hall",
     "description": "Part of the ceiling has fallen in, spilling rubble and pale tree roots across the floor."},
    {"name": "Crypt",
     "description": "Rows of stone sarcophagi line the walls. One lid has been pushed aside from within."},
    {"name": "Rune Chamber",
     "description": "The walls are carved with runes that hurt to look at for too long."},
    {"name": "Feast Hall",
     "description": "A long table is still set for a feast. The food turned to dust centuries ago."},
    {"name": "Windy Gallery",
     "description": "Wind moans through cracks in the stone, though there should be no wind this deep."},
    {"name": "Candle Shrine",
     "description": "Candle stubs cover every surface, as if someone held a vigil here for years."},
    {"name": "Well Room",
     "description": "A dry well sits in the middle of the room. Pebbles you drop into it never land."},
    {"name": "Goblin Den",
     "description": "Crude goblin graffiti covers the walls: crossed swords, a crown, a very rude drawing of a dwarf."},
    {"name": "Sloping Tunnel",
     "description": "The floor slopes gently downward and is slick with something dark."},
    {"name": "Empty Armory",
     "description": "The armory has been picked clean. Empty weapon racks line the walls like ribs."},
    {"name": "Cage Room",
     "description": "A great iron cage hangs from the ceiling on a creaking chain. Its door hangs open."},
    {"name": "Mushroom Garden",
     "description": "Mushrooms the size of shields grow in clusters, releasing slow puffs of golden spores."},
    {"name": "Abandoned Camp",
     "description": "A cold hearth holds the remains of a fire. Someone camped here, and left in a hurry."},
    {"name": "Mural Corridor",
     "description": "Faded murals show robed figures descending into the earth. You know how they felt."},
]

DEPTH_INTROS = [
    "The entrance hall of the old fortress. Torchlight from above barely reaches this far.",
    "The stonework grows rougher. These halls were dug by less careful hands.",
    "You smell damp earth and old blood. The fortress's dungeons lie around you.",
    "The catacombs. The dead were laid to rest here. Not all of them stayed that way.",
    "Ancient halls older than the fortress above. The air hums with something you cannot name.",
    "The deep dark. Few who come this far ever see the sun again.",
]

# Played when a wandering monster interrupts your rest.
REST_INTERRUPTED = [
    "You hear footsteps scraping toward you in the dark...",
    "Your eyes snap open. Something is coming.",
]
