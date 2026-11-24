"""
Character Selection Screen
Dedicated, clean, Game Boy-styled screen to browse, preview, and select
playable characters with matching portraits, names, stats, and animated sprites.
"""
import pygame
from game.settings import (
    GAME_W, GAME_H, COLOR_DARKEST, COLOR_DARK, COLOR_LIGHT, COLOR_LIGHTEST,
    KEYS_LEFT, KEYS_RIGHT, KEYS_UP, KEYS_DOWN, KEYS_CONFIRM, KEYS_INTERACT, KEYS_CANCEL
)
from game.fonts import font_heading, font_subheading, font_tag, font_body_small
from game.character_registry import get_all_characters, get_character, load_portrait
from game.ocean_animator import OceanCharacterAnimator


class CharacterSelectScreen:
    """
    Renders an authentic 160x144 Game Boy character selection interface.
    Features:
    - 4x2 grid of character portraits with high-contrast highlight cursor.
    - Large character preview (portrait + 8 FPS walking sprite).
    - Character name, class title, and description.
    - Full keyboard, D-pad, and touch support.
    """

    def __init__(self, ui, initial_char_id="actor1_character_01"):
        self.ui = ui
        self.characters = get_all_characters()
        self.selected_index = 0
        self.set_by_id(initial_char_id)

        self.done = False
        self.canceled = False
        self.blink_timer = 0
        self.blink_state = True

        # Walking animators for each character preview (animated at 8 FPS)
        self.animators = {}
        for c in self.characters:
            cid = c["id"]
            anim = OceanCharacterAnimator(cid, variant="gameboy", target_size=(24, 32), fps=8)
            anim.face("down")
            self.animators[cid] = anim

        # Touch hitboxes in native 160x144 space
        self.grid_rects = []
        self._init_layout()

    def _init_layout(self):
        self.grid_rects = []
        grid_x = 6
        grid_y = 78
        col_w = 36
        row_h = 24
        for idx in range(len(self.characters)):
            row = idx // 4
            col = idx % 4
            x = grid_x + col * col_w
            y = grid_y + row * row_h
            self.grid_rects.append(pygame.Rect(x, y, 34, 22))

        # Action button hitboxes
        self.confirm_btn_rect = pygame.Rect(4, 128, 72, 14)
        self.cancel_btn_rect = pygame.Rect(84, 128, 72, 14)

    def set_by_id(self, char_id):
        for i, c in enumerate(self.characters):
            if c["id"] == char_id:
                self.selected_index = i
                return
        self.selected_index = 0

    def get_selected_character(self):
        return self.characters[self.selected_index]

    def get_selected_id(self):
        return self.characters[self.selected_index]["id"]

    def reset(self, initial_char_id=None):
        if initial_char_id:
            self.set_by_id(initial_char_id)
        self.done = False
        self.canceled = False
        self.blink_timer = 0
        self.blink_state = True

    def handle_event(self, event, audio_mgr=None):
        if event.type == pygame.KEYDOWN:
            old_index = self.selected_index
            row = self.selected_index // 4
            col = self.selected_index % 4

            if any(event.key == k for k in KEYS_LEFT):
                col = (col - 1) % 4
                self.selected_index = row * 4 + col
            elif any(event.key == k for k in KEYS_RIGHT):
                col = (col + 1) % 4
                self.selected_index = row * 4 + col
            elif any(event.key == k for k in KEYS_UP):
                row = (row - 1) % 2
                self.selected_index = row * 4 + col
            elif any(event.key == k for k in KEYS_DOWN):
                row = (row + 1) % 2
                self.selected_index = row * 4 + col
            elif event.key in (pygame.K_PAGEUP, pygame.K_q):
                self.selected_index = (self.selected_index - 1) % len(self.characters)
            elif event.key in (pygame.K_PAGEDOWN, pygame.K_e, pygame.K_TAB):
                self.selected_index = (self.selected_index + 1) % len(self.characters)
            elif event.key in KEYS_CONFIRM or event.key in KEYS_INTERACT:
                if audio_mgr:
                    audio_mgr.play_sfx("menu_select", "ui")
                self.done = True
                return
            elif event.key in KEYS_CANCEL:
                if audio_mgr:
                    audio_mgr.play_sfx("menu_cancel", "ui")
                self.canceled = True
                self.done = True
                return

            if self.selected_index != old_index:
                if audio_mgr:
                    audio_mgr.play_sfx("menu_move", "ui")

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Map window/touch coordinates to 160x144 space if needed
            # (handled by caller passing native coordinates or direct rect check)
            mx, my = event.pos
            self.handle_pointer_down(mx, my, audio_mgr)

    def handle_pointer_down(self, native_x, native_y, audio_mgr=None):
        """Processes touch / click within native 160x144 coordinates."""
        for idx, rect in enumerate(self.grid_rects):
            if rect.collidepoint(native_x, native_y):
                if self.selected_index == idx:
                    # Tapping already selected character confirms it
                    if audio_mgr:
                        audio_mgr.play_sfx("menu_select", "ui")
                    self.done = True
                else:
                    self.selected_index = idx
                    if audio_mgr:
                        audio_mgr.play_sfx("menu_move", "ui")
                return True

        if self.confirm_btn_rect.collidepoint(native_x, native_y):
            if audio_mgr:
                audio_mgr.play_sfx("menu_select", "ui")
            self.done = True
            return True

        if self.cancel_btn_rect.collidepoint(native_x, native_y):
            if audio_mgr:
                audio_mgr.play_sfx("menu_cancel", "ui")
            self.canceled = True
            self.done = True
            return True

        return False

    def update(self, dt_ms):
        self.blink_timer += dt_ms
        if self.blink_timer >= 260:
            self.blink_timer -= 260
            self.blink_state = not self.blink_state

        # Update walking preview of the currently selected character
        cur_id = self.get_selected_id()
        if cur_id in self.animators:
            # Advance walk cycle in place
            self.animators[cur_id].update(dt_ms, moving=True, direction="down")

    def draw(self, surface):
        surface.fill(COLOR_LIGHTEST)

        # 1. Top Header Banner
        pygame.draw.rect(surface, COLOR_DARKEST, (0, 0, 160, 14))
        f_sub = font_subheading()
        title_txt = f_sub.render("= SELECT HERO =", False, COLOR_LIGHTEST)
        surface.blit(title_txt, ((160 - title_txt.get_width()) // 2, 2))

        cur = self.get_selected_character()
        cur_id = cur["id"]

        # 2. Left Preview Panel (Portrait + Walking Animated Sprite)
        # Box: x=4, y=17, w=68, h=56
        pygame.draw.rect(surface, COLOR_LIGHT, (4, 17, 68, 56))
        pygame.draw.rect(surface, COLOR_DARKEST, (4, 17, 68, 56), 1)

        # Large Portrait (32x32)
        port_32 = load_portrait(cur, size=(32, 32))
        surface.blit(port_32, (8, 20))
        pygame.draw.rect(surface, COLOR_DARKEST, (7, 19, 34, 34), 1)

        # Animated Walking Sprite (24x32)
        anim = self.animators.get(cur_id)
        if anim:
            sprite_frame = anim.get_frame()
            surface.blit(sprite_frame, (44, 21))

        # Bottom label inside preview box: Class title
        f_tag = font_tag()
        class_badge = f_tag.render(cur["class_name"].upper(), False, COLOR_DARKEST)
        surface.blit(class_badge, ((4 + 68 - class_badge.get_width()) // 2, 57))

        # 3. Right Information Panel
        # Box: x=75, y=17, w=81, h=56
        pygame.draw.rect(surface, COLOR_LIGHT, (75, 17, 81, 56))
        pygame.draw.rect(surface, COLOR_DARKEST, (75, 17, 81, 56), 1)

        f_name = font_heading()
        f_body = font_body_small()

        # Name & Title
        name_txt = f_name.render(cur["name"].upper(), False, COLOR_DARKEST)
        surface.blit(name_txt, (79, 20))

        title_txt = f_body.render(cur["title"], False, COLOR_DARK)
        surface.blit(title_txt, (79, 31))

        # Description (split if long)
        desc = cur["description"]
        if len(desc) > 20:
            words = desc.split()
            l1, l2 = "", ""
            for w in words:
                if len(l1 + " " + w) <= 17:
                    l1 = (l1 + " " + w).strip()
                else:
                    l2 = (l2 + " " + w).strip()
            surface.blit(f_body.render(l1, False, COLOR_DARKEST), (79, 43))
            surface.blit(f_body.render(l2, False, COLOR_DARKEST), (79, 52))
        else:
            surface.blit(f_body.render(desc, False, COLOR_DARKEST), (79, 45))

        # 4. Selection Grid of 8 Portraits (4 columns x 2 rows)
        grid_container = pygame.Rect(3, 75, 154, 50)
        pygame.draw.rect(surface, COLOR_LIGHT, grid_container)
        pygame.draw.rect(surface, COLOR_DARKEST, grid_container, 1)

        for idx, (c, rect) in enumerate(zip(self.characters, self.grid_rects)):
            is_selected = (idx == self.selected_index)

            # Slot background
            bg_col = COLOR_LIGHTEST if is_selected else COLOR_LIGHT
            pygame.draw.rect(surface, bg_col, rect)

            # Thumbnail portrait (18x18)
            thumb = load_portrait(c, size=(18, 18))
            surface.blit(thumb, (rect.x + 2, rect.y + 2))

            # Number label
            num_str = str(idx + 1)
            num_color = COLOR_DARKEST if is_selected else COLOR_DARK
            surface.blit(f_body.render(num_str, False, num_color), (rect.x + 23, rect.y + 6))

            # Border & Selection Cursor
            if is_selected:
                # High-contrast selection box with cursor
                pygame.draw.rect(surface, COLOR_DARKEST, rect, 2)
                if self.blink_state:
                    # Flashing corner markers
                    pygame.draw.rect(surface, COLOR_DARKEST, (rect.x - 1, rect.y - 1, 4, 2))
                    pygame.draw.rect(surface, COLOR_DARKEST, (rect.right - 3, rect.y - 1, 4, 2))
                    pygame.draw.rect(surface, COLOR_DARKEST, (rect.x - 1, rect.bottom - 1, 4, 2))
                    pygame.draw.rect(surface, COLOR_DARKEST, (rect.right - 3, rect.bottom - 1, 4, 2))
            else:
                pygame.draw.rect(surface, COLOR_DARK, rect, 1)

        # 5. Footer Buttons / Prompts
        # Confirm Button (left)
        pygame.draw.rect(surface, COLOR_DARKEST, self.confirm_btn_rect)
        btn_txt = f_tag.render("A: CONFIRM", False, COLOR_LIGHTEST)
        surface.blit(btn_txt, (self.confirm_btn_rect.x + (self.confirm_btn_rect.w - btn_txt.get_width()) // 2,
                               self.confirm_btn_rect.y + 3))

        # Cancel Button (right)
        pygame.draw.rect(surface, COLOR_DARK, self.cancel_btn_rect)
        back_txt = f_tag.render("B: BACK", False, COLOR_LIGHTEST)
        surface.blit(back_txt, (self.cancel_btn_rect.x + (self.cancel_btn_rect.w - back_txt.get_width()) // 2,
                                self.cancel_btn_rect.y + 3))
