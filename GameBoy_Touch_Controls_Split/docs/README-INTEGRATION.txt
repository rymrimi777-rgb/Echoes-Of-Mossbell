GAME BOY-STYLE KEYBOARD BUTTON ASSETS
Organized for integration into a Python + Pygame project.

FOLDER GUIDE
- controls/dpad/              Directional buttons (Up, Down, Left, Right)
- controls/action_buttons/    Main action buttons (A, B)
- controls/extra_buttons/     Optional X and Y buttons
- controls/system_buttons/    Start and Select
- sprite_sheets/              Combined button animation sheet
- preview/                    Full keyboard-keys preview image
- documentation/              Original creator README

IMPORTANT
These PNG files are visual assets only. They do not implement touch input by
themselves. In Pygame, the developer/agent must load the images, draw them,
detect finger or mouse/touch events, and connect each button to game actions.

The individual tileset PNGs are sprite strips (not necessarily single images).
Inspect their dimensions and frames before slicing or scaling. Preserve
transparency and pixel-art proportions; use nearest-neighbor scaling.

Suggested default mapping:
- D-pad: move player
- A: interact / confirm / advance dialogue
- B: cancel / back
- Start: pause / open menu
- Select: inventory or secondary menu
- X and Y: optional actions only if the game needs them

Keep the original README in documentation/.
Check the asset creator's page/license before public or commercial release:
https://okutasan.itch.io/
