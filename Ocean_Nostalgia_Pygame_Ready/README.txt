OCEAN'S NOSTALGIA - VX HEROES
Pygame-ready character organization

CONTENTS
- characters/: 24 individual character folders (3 source sheets x 8 character slots).
- Each character has three visual variants:
  gameboy/  : monochrome Game Boy-style version (-GB source)
  color/    : color version
  gray/     : grayscale version
- Each variant contains:
  *_sheet.png             Full 3-column x 4-row character sheet.
  *_walk_down.png         3-frame horizontal strip facing down.
  *_walk_left.png         3-frame horizontal strip facing left.
  *_walk_right.png        3-frame horizontal strip facing right.
  *_walk_up.png           3-frame horizontal strip facing up.
  frames/<direction>/     Individual PNG frame_00.png, frame_01.png, frame_02.png.
  animation.json          Exact frame dimensions, direction mapping, and suggested FPS.

FRAME LAYOUT
- This package uses the RPG Maker MV-sized source assets only.
- Original MV source sheets are 864 x 768 pixels.
- Each source frame is 72 x 96 pixels.
- Each character slot is 3 columns x 4 rows = 216 x 384 pixels.
- The 12 x 8 source sheet contains 4 character slots across and 2 down.
- Direction rows: row 0 = down, row 1 = left, row 2 = right, row 3 = up.
- Each direction has 3 animation frames, ordered left-to-right.
- Suggested animation speed: 8 FPS (adjust after playtesting).
- Transparent backgrounds are preserved. Do not use smooth scaling; use nearest-neighbor.

NAMING
- actor1_character_01 ... actor1_character_08 come from Actor1RMVX.
- actor2_character_01 ... actor2_character_08 come from Actor2RMVX.
- actor3_character_01 ... actor3_character_08 come from Actor3RMVX.
- The numeric slot order follows the original source sheet, left-to-right then top-to-bottom.

IMPORTANT
- This is an asset extraction/organization package, not a complete game or engine plugin.
- These are RPG Maker MV-layout assets organized for a custom Python/Pygame project.
- Choose one variant per character (gameboy, color, or gray); do not mix different variants for the same in-game character unless intentional.
- Keep this directory structure when giving it to your coding agent.
- Review LICENSE_AND_CREDIT.txt before publishing or distributing your game.
- The creator's terms require credit to Ocean's Dream and state that you must own the original RPG Maker VX RTP because these assets are based on its characters. The terms also restrict redistributing this asset pack to others; link to the original itch.io page instead.
