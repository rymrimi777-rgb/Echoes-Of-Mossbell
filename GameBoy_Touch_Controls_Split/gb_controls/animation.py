"""Button movement (press / release) - kept apart from the button itself.

Frames come from assets/buttons/<group>/<name>/ :
    0 = idle.png     (raised)
    1 = mid.png      (half pressed)
    2 = pressed.png  (fully pressed)
"""

IDLE, PRESSING, PRESSED, RELEASING = "idle", "pressing", "pressed", "releasing"
FRAME_FOR_STATE = {IDLE: 0, PRESSING: 1, PRESSED: 2, RELEASING: 1}
STEP_MS = 45


class ButtonAnimation:
    def __init__(self, step_ms=STEP_MS):
        self.step_ms = step_ms
        self.state = IDLE
        self._timer = 0
        self._release_queued = False

    def press(self):
        if self.state in (IDLE, RELEASING):
            self.state, self._timer = PRESSING, 0
        self._release_queued = False

    def release(self):
        if self.state == PRESSED:
            self.state, self._timer = RELEASING, 0
        elif self.state == PRESSING:
            # very short tap: let the pressed frame show before going back up
            self._release_queued = True

    def update(self, dt_ms):
        waiting = self.state in (PRESSING, RELEASING) or (
            self.state == PRESSED and self._release_queued
        )
        if not waiting:
            return
        self._timer += dt_ms
        if self._timer < self.step_ms:
            return
        self._timer = 0
        if self.state == PRESSING:
            self.state = PRESSED
        elif self.state == PRESSED:  # queued release
            self.state, self._release_queued = RELEASING, False
        else:  # RELEASING
            self.state = IDLE

    @property
    def frame_index(self):
        return FRAME_FOR_STATE[self.state]
