# How to use
Each `characters/<name>.png` is a sheet of 16x16 frames. Row order and frame counts are in the JSON next to it.
Walk cycles are 8 frames at about 110 ms; idle is 4 frames (breathing + blink). Left is a mirror of right, shipped ready-made.
Portraits are 32x32 and fit inside `ui/portrait_frame_40.png`. Play frame 1 (talking) and 0 alternately while text types out; frame 2 is a blink.
The dialogue box is 160x48, the width of a 160x144 handheld screen.

## Suggested timings
- Walk: 8 frames x 110 ms (about 1 tile per cycle at 16 px/s for a slow walk, or 4 frames x 2 speed for running).
- Idle: 4 frames x 250 ms. Frame 3 holds a blink on the down-facing idle.
- Talking portrait: swap frames 0 and 1 every 120 ms while letters appear, then show frame 0. Add frame 2 now and then for a blink.

## Building a scene
1. Place characters on a 16x16 grid. Their feet sit on the bottom row of the frame, so a character standing on tile (x, y) is drawn at (x*16, y*16).
2. Sort characters by their y position each frame so the lower one is drawn in front.
3. Show the dialogue box at the bottom of the screen (y = 96 on a 144-high screen), the portrait frame at (4, 100) and the portrait at (8, 104).
4. Use the next-arrow strip in the bottom right corner to tell the player to press a button.

## Recolouring
All images use exactly 4 shades. To make a new palette, map shade 1 (darkest) to 4 (lightest) to your own colours. The .gpl files load in Aseprite, GIMP and Krita.

## Engine import tips (general guidance - no engine project files are included)
- **Godot 4:** set the default texture filter to *Nearest*. Slice `_stripN.png` into N frames (frame size in the JSON next to it) with `AnimatedSprite2D`. Tiles go into a `TileSet` with 16x16 tiles.
- **Unity:** Filter Mode *Point*, Compression *None*, Pixels Per Unit 16. Slice in the Sprite Editor (Grid By Cell Size).
- **GameMaker:** Import Strip Image with frame count = the N in `_stripN`; turn off texture interpolation.
- **Authentic handheld look:** run your game at 160x144 and scale up by a whole number (x3 = 480x432, x5 = 800x720).
- **Palette swap:** every folder holds the same art in a different 4-shade palette. Because each image uses only shades 1-4, a simple palette-swap shader can switch palettes at runtime (darkest = shade 1).
