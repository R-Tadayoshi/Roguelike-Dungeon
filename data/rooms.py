"""Atmospheric flavor text.

ROOM_DESCRIPTIONS: each room on a floor gets one, shown the first time you step inside.
Keep at least as many entries as map_gen.MAX_ROOMS so a floor never repeats itself.

DEPTH_INTROS: shown on arriving at a depth. Depths past the end of the list reuse the last line.
"""

ROOM_DESCRIPTIONS = [
    "Cold water drips from the vaulted ceiling into a shallow, stagnant pool.",
    "Rusted manacles hang from the walls. Someone scratched tally marks beside them, hundreds of them.",
    "A toppled altar lies in pieces. The air still smells faintly of incense and ash.",
    "Cobwebs thick as curtains drape the corners. Something large spun these.",
    "The floor is littered with gnawed bones. Most of them are small. Most of them.",
    "A faded tapestry shows a knight slaying a dragon. Someone has slashed out the knight's face.",
    "Old barrels line one wall, their staves split and their contents long since spoiled.",
    "A cracked mosaic of a sun covers the floor. It is the only warm color you have seen in hours.",
    "Burnt-out torches sit in iron sconces. The soot above them is fresh.",
    "This was a library once. Mouldering pages crunch underfoot like dead leaves.",
    "An empty suit of armor stands sentinel in the corner. You could swear its helm just turned.",
    "Moss grows thick and green here, glowing with a faint, sickly light.",
    "A collapsed section of ceiling has spilled rubble and tree roots into the room.",
    "Rows of stone sarcophagi line the walls. One lid has been pushed aside from within.",
    "The walls are carved with runes that hurt to look at for too long.",
    "A long feasting table is still set for a meal. The food turned to dust centuries ago.",
    "Wind moans through cracks in the stone, though there should be no wind this deep.",
    "Dozens of candle stubs cover every surface, as if someone held a vigil here for years.",
    "A dry well sits in the middle of the room. Pebbles you drop into it never land.",
    "Crude goblin graffiti covers the walls: crossed swords, a crown, a very rude drawing of a dwarf.",
    "The floor slopes gently downward and is slick with something dark.",
    "An armory, picked clean. Empty weapon racks line the walls like ribs.",
    "A great iron cage hangs from the ceiling on a creaking chain. The door hangs open.",
    "Mushrooms the size of shields grow in clusters, releasing slow puffs of golden spores.",
    "A cold hearth holds the remains of a fire. Someone camped here, and left in a hurry.",
    "Faded murals depict a procession of robed figures descending into the earth. You know how they felt.",
]

DEPTH_INTROS = [
    "The entrance hall of the old fortress. Torchlight from above barely reaches this far.",
    "The stonework grows rougher. These halls were dug by less careful hands.",
    "You smell damp earth and old blood. The fortress's dungeons lie around you.",
    "The catacombs. The dead were laid to rest here. Not all of them stayed that way.",
    "Ancient halls older than the fortress above. The air hums with something you cannot name.",
    "The deep dark. Few who come this far ever see the sun again.",
]
