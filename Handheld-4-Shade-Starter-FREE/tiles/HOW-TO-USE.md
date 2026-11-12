# How to use the Handheld 4-Shade Top-Down Adventure Tileset

## Tile size and screen
Everything is on a 16x16 grid. Props bigger than one tile (trees 32x32, buildings 48x48 and up, beds 16x32) are single PNGs
that you place on top of the ground layer. For the authentic look, render at 160x144 (10 x 9 tiles) and scale by a whole number.

## Layers we suggest
1. Ground (grass, cobbles, floors - pick random variants so large areas do not look repeated)
2. Auto-tile terrains (path, water, sand, ledge, hedge, wall, pit, lava, rug)
3. Props and buildings (draw the small contact shadow under them - it is already part of the mockups' style)

## Corner-Wang auto-tiles
Each `autotile_*.png` holds 16 tiles in a 4x4 grid. Tile index = NW*1 + NE*2 + SW*4 + SE*8, where a corner bit is 1 if that
corner is the second terrain (path, water, wall...). Index 0 is plain first terrain, 15 is plain second terrain.
- **Godot 4:** add the sheet to a TileSet, create a Terrain Set in *Match Corners* mode, and paint the peering bits from the JSON.
- **Tiled:** create a Wang set of type *Corner* and mark corners from the JSON (or by eye: the sheet order is fixed).
- **Unity:** use a Rule Tile with corner rules, or place tiles by index from your own map code.
- **Code:** store your map as a grid of corners (one bigger than the tile grid) and compute each tile index from its 4 corners.

## Animated tiles
`anim_water_autotile_strip4.png` is the water auto-tile sheet in 4 frames (each frame is a full 4x4 sheet, 64x64).
Use the same tile index in every frame. Torches, spike traps, fireplace, flowers and lava are simple strips.

## Palettes
Every palette folder has identical file names, so you can switch the whole game's look by changing one folder path,
or keep one folder and use a palette-swap shader: shade 1 = darkest ... shade 4 = lightest.

## Engine import tips (general guidance - no engine project files are included)
- **Godot 4:** set the default texture filter to *Nearest*. Slice `_stripN.png` into N frames (frame size in the JSON next to it) with `AnimatedSprite2D`. Tiles go into a `TileSet` with 16x16 tiles.
- **Unity:** Filter Mode *Point*, Compression *None*, Pixels Per Unit 16. Slice in the Sprite Editor (Grid By Cell Size).
- **GameMaker:** Import Strip Image with frame count = the N in `_stripN`; turn off texture interpolation.
- **Authentic handheld look:** run your game at 160x144 and scale up by a whole number (x3 = 480x432, x5 = 800x720).
- **Palette swap:** every folder holds the same art in a different 4-shade palette. Because each image uses only shades 1-4, a simple palette-swap shader can switch palettes at runtime (darkest = shade 1).
