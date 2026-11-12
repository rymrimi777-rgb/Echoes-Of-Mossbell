"""
Dialogue system – paginated typewriter text using Pixel Operator,
animated portraits, and Game Boy layout.
"""
import pygame, os
from game.settings import (GAME_W, GAME_H, COLOR_DARKEST, COLOR_DARK,
                           COLOR_LIGHT, COLOR_LIGHTEST, UI_DIR, SPRITE_DIR,
                           KEYS_INTERACT, KEYS_CONFIRM, KEYS_CANCEL)
from game.animation import load_image, PortraitAnimator
from game.fonts import font_dialogue, font_tag


def paginate_dialogue(text, max_w, font, max_lines_per_page=2):
    """
    Splits text into pages where each page has at most `max_lines_per_page` lines,
    ensuring each line fits within `max_w` pixels.
    """
    paragraphs = text.replace("\r", "").split("\n")
    all_lines = []
    for p in paragraphs:
        words = p.split()
        if not words:
            continue
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    all_lines.append(cur)
                cur = w
        if cur:
            all_lines.append(cur)

    if not all_lines:
        return [["..."]]

    pages = []
    for i in range(0, len(all_lines), max_lines_per_page):
        pages.append(all_lines[i : i + max_lines_per_page])
    return pages


class DialogueBox:
    """
    Authentic Game Boy 160x48 dialogue box renderer at the bottom of the screen.
    Uses Pixel Operator for body dialogue and Press Start 2P for indicators.
    """

    def __init__(self):
        bg_path = os.path.join(UI_DIR, "dialog_box_160x48.png")
        if os.path.isfile(bg_path):
            self.bg = load_image(bg_path)
        else:
            self.bg = pygame.Surface((160, 48))
            self.bg.fill(COLOR_LIGHTEST)
            pygame.draw.rect(self.bg, COLOR_DARKEST, (0, 0, 160, 48), 2)

        # Portrait animators
        self.portrait_animators = {}
        for name in ("hero", "boy", "king", "old_man"):
            p_path = os.path.join(SPRITE_DIR, f"{name}_talk_strip3.png")
            self.portrait_animators[name] = PortraitAnimator(p_path)

        # Typography
        self.font = font_dialogue()
        self.font_indicator = font_tag()

        # State
        self.active = False
        self.entries = []
        self.entry_index = 0
        self.pages = []
        self.page_index = 0
        self.revealed_chars = 0
        self.char_timer = 0
        self.chars_per_sec = 36
        self.is_page_finished = False
        self.callback = None
        self.arrow_timer = 0
        self.show_arrow = True

    def start(self, entries, callback=None):
        self.active = True
        self.entries = []
        for e in entries:
            if isinstance(e, str):
                self.entries.append({"text": e, "portrait": None})
            else:
                self.entries.append(e)

        self.entry_index = 0
        self.callback = callback
        self._load_current_entry()

    def _load_current_entry(self):
        cur = self.entries[self.entry_index]
        text = cur.get("text", "")
        portrait = cur.get("portrait")

        if portrait and portrait in self.portrait_animators:
            max_w = 108
        else:
            max_w = 142

        self.pages = paginate_dialogue(text, max_w, self.font, max_lines_per_page=2)
        self.page_index = 0
        self.revealed_chars = 0
        self.char_timer = 0
        self.is_page_finished = False

    def is_active(self):
        return self.active

    def close(self):
        self.active = False
        cb = self.callback
        self.callback = None
        if cb:
            cb()

    def handle_event(self, event, touch_confirm=False, audio_mgr=None):
        if not self.active:
            return

        is_interact = False
        is_cancel = False

        if touch_confirm:
            is_interact = True
        elif event and event.type == pygame.KEYDOWN:
            if event.key in KEYS_INTERACT or event.key in KEYS_CONFIRM:
                is_interact = True
            elif event.key in KEYS_CANCEL:
                is_cancel = True

        if is_interact:
            total_chars = sum(len(line) for line in self.pages[self.page_index])
            if not self.is_page_finished:
                self.revealed_chars = total_chars
                self.is_page_finished = True
            else:
                if audio_mgr:
                    audio_mgr.play_sfx("menu_select", "ui")
                self.page_index += 1
                if self.page_index < len(self.pages):
                    self.revealed_chars = 0
                    self.char_timer = 0
                    self.is_page_finished = False
                else:
                    self.entry_index += 1
                    if self.entry_index < len(self.entries):
                        self._load_current_entry()
                    else:
                        self.close()

        elif is_cancel:
            total_chars = sum(len(line) for line in self.pages[self.page_index])
            if not self.is_page_finished:
                self.revealed_chars = total_chars
                self.is_page_finished = True
            else:
                if audio_mgr:
                    audio_mgr.play_sfx("menu_cancel", "ui")
                self.entry_index += 1
                if self.entry_index < len(self.entries):
                    self._load_current_entry()
                else:
                    self.close()

    def update(self, dt_ms, audio_mgr=None):
        if not self.active:
            return

        cur = self.entries[self.entry_index]
        portrait = cur.get("portrait")
        current_page_lines = self.pages[self.page_index]
        total_chars = sum(len(line) for line in current_page_lines)

        if self.revealed_chars < total_chars:
            self.char_timer += dt_ms
            ms_per_char = 1000 / self.chars_per_sec
            chars_to_add = int(self.char_timer // ms_per_char)
            if chars_to_add > 0:
                self.revealed_chars = min(total_chars, self.revealed_chars + chars_to_add)
                self.char_timer %= ms_per_char
                if audio_mgr:
                    audio_mgr.play_sfx("talk_blip", "npc")
            is_typing = (self.revealed_chars < total_chars)
        else:
            self.is_page_finished = True
            is_typing = False

        if portrait and portrait in self.portrait_animators:
            self.portrait_animators[portrait].update(dt_ms, is_typing)

        self.arrow_timer += dt_ms
        if self.arrow_timer >= 240:
            self.arrow_timer -= 240
            self.show_arrow = not self.show_arrow

    def draw(self, surface):
        if not self.active:
            return

        box_y = GAME_H - 48
        surface.blit(self.bg, (0, box_y))

        cur = self.entries[self.entry_index]
        portrait = cur.get("portrait")

        if portrait and portrait in self.portrait_animators:
            p_surf = self.portrait_animators[portrait].get_frame()
            surface.blit(p_surf, (6, box_y + 8))
            text_x = 42
        else:
            text_x = 8

        lines = self.pages[self.page_index]
        remaining = self.revealed_chars
        line_y = box_y + 8

        for line in lines:
            if remaining <= 0:
                break
            visible_text = line[:remaining]
            remaining -= len(line)
            s = self.font.render(visible_text, False, COLOR_DARKEST)
            surface.blit(s, (text_x, line_y))
            line_y += 15

        # Blinking advance indicator (▼)
        if self.is_page_finished and self.show_arrow:
            arrow = self.font_indicator.render("v", False, COLOR_DARKEST)
            surface.blit(arrow, (GAME_W - 12, GAME_H - 10))
