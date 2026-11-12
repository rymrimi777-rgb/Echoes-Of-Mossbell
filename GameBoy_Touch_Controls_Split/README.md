# GameBoy Touch Controls (split version)

Assets: "GBStudio Keyboard Buttons" by Luna Desuwa (https://okutasan.itch.io).
Check the creator's page/license before any public or commercial release.
Original docs are kept in `docs/`.

## Layout

```
assets/buttons/<group>/<name>/
    idle.png        frame 0 - raised
    mid.png         frame 1 - half pressed
    pressed.png     frame 2 - fully pressed
    <name>_strip.png   original strip (untouched)
assets/reference/   full sprite sheet + preview

gb_controls/
    animation.py    the movement (idle -> pressing -> pressed -> releasing)
    base_button.py  TouchButton: loads frames, draws, hit-test, press/release
    buttons/        ONE FILE PER BUTTON: up, down, left, right, a, b, x, y, start, select
    controller.py   multi-touch routing + default layout
    events.py       GB_BUTTON_DOWN / GB_BUTTON_UP
demo.py
```

Groups: `dpad` (up/down/left/right), `action` (a/b), `extra` (x/y), `system` (start/select).
Frame size: 16x16 (32x16 for start/select).

## Use

```python
from gb_controls import build_default_controller, GB_BUTTON_DOWN, GB_BUTTON_UP

screen = pygame.display.set_mode(SIZE)          # BEFORE building the controller
controller = build_default_controller(SIZE, scale=3)

# game loop
for event in pygame.event.get():
    controller.handle_event(event, SIZE)
    if event.type == GB_BUTTON_DOWN and event.action == "a":
        ...                                     # interact / confirm
if controller.is_pressed("left"):
    player.x -= speed
controller.update(dt_ms)
controller.draw(screen)
```

Change a button's look or feel: edit its own file in `gb_controls/buttons/`
(sprite folder + action name). Change the movement for ALL buttons: `animation.py`
(`STEP_MS` = speed of each frame).
