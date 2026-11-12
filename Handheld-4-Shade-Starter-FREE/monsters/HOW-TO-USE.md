# How to use
Every sheet has one row per animation; frame size, row order and frame counts are in the JSON next to it.

## Animations
- **idle** 4 frames x 160 ms, loops.
- **move** 4 frames x 120 ms, loops. Ground monsters step 1 px side to side; flyers flap.
- **attack** 6 frames x 100 ms: frames 1-2 are the wind-up (the monster leans back), 3-4 the strike, 5 the recovery. Trigger damage on frame 3.
- **hurt** 4 frames x 70 ms: white flash, knock-back, normal, flash. Play once.
- **death** 6 frames (8 for bosses) x 90 ms: a dithered dissolve. Play once, then remove the monster.

## Variants
Each family has 3 variants (normal, dark, elite) with different shading and features, so you can scale difficulty across your game.

## Battle screen
The ui/ folder has a 160x40 text box (sits at the bottom of a 160x144 screen, y = 104), an 80x48 menu box,
an HP bar with 7 fill states (frame 0 = empty, frame 6 = full) and a 2-frame cursor. fx/ has hit effects to play over a monster.
Place bosses in the top half of the screen, centred, with the text box below.

## Recolouring
All images use exactly 4 shades. Map shade 1 (darkest) to 4 (lightest) to your own colours, or use the .gpl files in Aseprite, GIMP or Krita.

## Engine import tips (general guidance - no engine project files are included)
- **Godot 4:** set the default texture filter to *Nearest*. Slice `_stripN.png` into N frames (frame size in the JSON next to it) with `AnimatedSprite2D`. Tiles go into a `TileSet` with 16x16 tiles.
- **Unity:** Filter Mode *Point*, Compression *None*, Pixels Per Unit 16. Slice in the Sprite Editor (Grid By Cell Size).
- **GameMaker:** Import Strip Image with frame count = the N in `_stripN`; turn off texture interpolation.
- **Authentic handheld look:** run your game at 160x144 and scale up by a whole number (x3 = 480x432, x5 = 800x720).
- **Palette swap:** every folder holds the same art in a different 4-shade palette. Because each image uses only shades 1-4, a simple palette-swap shader can switch palettes at runtime (darkest = shade 1).
