# How to use
Use `atlases/` if your engine likes sprite sheets (the JSON gives each icon's rectangle), or `single/` if you prefer one file per item.
Icon names are `<category>_<number>.png` and stay the same in every palette folder, so your item database can store one name.

## Inventory screens
- `ui/inventory_window_160x144.png` fills a 160x144 screen. Put a grid of `ui/slot_20.png` inside it (7 across fits, 2 px apart, starting at x = 8).
- Draw an icon at slot position + 2. Use `slot_20_selected.png` and the 2-frame `slot_cursor_24` strip (drawn at slot position - 2) for the selected slot.
- `ui/info_box_160x32.png` holds the item name and description at the bottom of the screen.

## Animated items
Each strip in `animated/` is 4 frames of 16x16. Play at about 130 ms per frame for pickups, shop displays or treasure reveals.

## Variety
Families are built from shared parts (blades, hilts, heads, gems, liquids), so items in a category look like a set: use darker shades for weaker items and lighter or gem-set versions for rarer ones.

## Recolouring
All icons use exactly 4 shades (shade 1 darkest, shade 4 lightest). Map them to your own colours or use the .gpl files in Aseprite, GIMP or Krita.

## Engine import tips (general guidance - no engine project files are included)
- **Godot 4:** set the default texture filter to *Nearest*. Slice `_stripN.png` into N frames (frame size in the JSON next to it) with `AnimatedSprite2D`. Tiles go into a `TileSet` with 16x16 tiles.
- **Unity:** Filter Mode *Point*, Compression *None*, Pixels Per Unit 16. Slice in the Sprite Editor (Grid By Cell Size).
- **GameMaker:** Import Strip Image with frame count = the N in `_stripN`; turn off texture interpolation.
- **Authentic handheld look:** run your game at 160x144 and scale up by a whole number (x3 = 480x432, x5 = 800x720).
- **Palette swap:** every folder holds the same art in a different 4-shade palette. Because each image uses only shades 1-4, a simple palette-swap shader can switch palettes at runtime (darkest = shade 1).
