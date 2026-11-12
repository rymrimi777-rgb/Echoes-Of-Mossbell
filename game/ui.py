"""
UI module – title screen, pause menu, categorized inventory with 16x16 icons,
quest log, animated HP bar, and transition effects.
Consistent retro typography:
- Press Start 2P for titles, headers, options, buttons, and status indicators.
- Pixel Operator for readable body text, descriptions, and lists.
"""
import pygame, os
from game.settings import (GAME_W, GAME_H, COLOR_DARKEST, COLOR_DARK,
                           COLOR_LIGHT, COLOR_LIGHTEST, UI_DIR,
                           KEYS_INTERACT, KEYS_CANCEL, KEYS_CONFIRM, KEYS_PAUSE,
                           KEYS_LEFT, KEYS_RIGHT, KEYS_UP, KEYS_DOWN)
from game.animation import load_image, slice_strip
from game.fonts import (font_title, font_heading, font_subheading,
                        font_tag, font_dialogue, font_body, font_body_small)


class UIRenderer:
    def __init__(self):
        # HP bar strip (336x6 -> 7 frames of 48x6)
        hp_path = os.path.join(UI_DIR, "hp_bar_48px_strip7.png")
        if os.path.isfile(hp_path):
            sheet = load_image(hp_path)
            self.hp_frames = slice_strip(sheet, 48, 6, 7)
        else:
            self.hp_frames = None

    def draw_box(self, surface, x, y, w, h, fill=COLOR_LIGHT, border=COLOR_DARKEST):
        pygame.draw.rect(surface, fill, (x, y, w, h))
        pygame.draw.rect(surface, border, (x, y, w, h), 1)

    def draw_text(self, surface, text, x, y, color=COLOR_DARKEST, font=None):
        f = font or font_body()
        s = f.render(text, False, color)
        surface.blit(s, (x, y))

    def draw_text_centered(self, surface, text, y, color=COLOR_DARKEST, font=None):
        f = font or font_body()
        s = f.render(text, False, color)
        surface.blit(s, ((GAME_W - s.get_width()) // 2, y))

    def draw_hp_bar(self, surface, x, y, cur_hp, max_hp):
        """Renders the authentic 48px handheld HP bar."""
        if self.hp_frames:
            ratio = max(0.0, min(1.0, cur_hp / max(1, max_hp)))
            frame_idx = int(round(ratio * 6))
            surface.blit(self.hp_frames[frame_idx], (x, y))
        else:
            pygame.draw.rect(surface, COLOR_DARKEST, (x, y, 48, 6), 1)
            fill_w = int(46 * (cur_hp / max(1, max_hp)))
            pygame.draw.rect(surface, COLOR_DARK, (x + 1, y + 1, fill_w, 4))


class TitleScreen:
    """Authentic Game Boy start screen."""
    def __init__(self, ui, save_exists=False):
        self.ui = ui
        self.options = ["NEW GAME"]
        if save_exists:
            self.options.insert(0, "CONTINUE")
        self.options.append("QUIT")
        self.index = 0
        self.done = False
        self.choice = None
        self.blink_timer = 0
        self.show_press = True

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if any(event.key == k for k in KEYS_UP):
            self.index = (self.index - 1) % len(self.options)
        elif any(event.key == k for k in KEYS_DOWN):
            self.index = (self.index + 1) % len(self.options)
        elif event.key in KEYS_INTERACT or event.key in KEYS_CONFIRM:
            self.choice = self.options[self.index]
            self.done = True

    def update(self, dt_ms):
        self.blink_timer += dt_ms
        if self.blink_timer > 400:
            self.blink_timer -= 400
            self.show_press = not self.show_press

    def draw(self, surface):
        surface.fill(COLOR_LIGHTEST)
        # Main Game Title (Press Start 2P)
        self.ui.draw_text_centered(surface, "ECHOES OF", 24, COLOR_DARKEST, font_title())
        self.ui.draw_text_centered(surface, "MOSSBELL", 40, COLOR_DARKEST, font_title())
        # Subtitle (Pixel Operator)
        self.ui.draw_text_centered(surface, "A Retro Handheld RPG", 58, COLOR_DARK, font_body())

        # Menu Options (Press Start 2P)
        start_y = 80
        for i, opt in enumerate(self.options):
            prefix = "> " if i == self.index else "  "
            color = COLOR_DARKEST if i == self.index else COLOR_DARK
            self.ui.draw_text_centered(surface, prefix + opt, start_y + i * 14, color, font_subheading())

        # Start prompt (Press Start 2P)
        if self.show_press:
            self.ui.draw_text_centered(surface, "[SPACE] START", 128, COLOR_DARK, font_tag())


class PauseMenu:
    def __init__(self, ui):
        self.ui = ui
        self.options = ["RESUME", "INVENTORY", "QUESTS", "SETTINGS", "SAVE", "QUIT"]
        self.index = 0
        self.done = False
        self.choice = None

        # Settings sub-mode
        self.sub_mode = "main"  # "main" or "settings"
        self.settings_options = ["Music", "SFX", "Mute", "Touch", "T.Size", "T.Alpha", "BACK"]
        self.settings_index = 0

    def reset(self):
        self.index = 0
        self.settings_index = 0
        self.sub_mode = "main"
        self.done = False
        self.choice = None

    def handle_event(self, event, audio_mgr=None, touch_ctrl=None):
        if event.type != pygame.KEYDOWN:
            return

        if self.sub_mode == "main":
            if event.key in KEYS_PAUSE or event.key in KEYS_CANCEL:
                if audio_mgr:
                    audio_mgr.play_sfx("menu_cancel", "ui")
                self.choice = "RESUME"
                self.done = True
            elif any(event.key == k for k in KEYS_UP):
                if audio_mgr:
                    audio_mgr.play_sfx("menu_move", "ui")
                self.index = (self.index - 1) % len(self.options)
            elif any(event.key == k for k in KEYS_DOWN):
                if audio_mgr:
                    audio_mgr.play_sfx("menu_move", "ui")
                self.index = (self.index + 1) % len(self.options)
            elif event.key in KEYS_INTERACT or event.key in KEYS_CONFIRM:
                opt = self.options[self.index]
                if opt == "SETTINGS":
                    if audio_mgr:
                        audio_mgr.play_sfx("menu_select", "ui")
                    self.sub_mode = "settings"
                    self.settings_index = 0
                else:
                    if audio_mgr:
                        audio_mgr.play_sfx("menu_select", "ui")
                    self.choice = opt
                    self.done = True

        elif self.sub_mode == "settings":
            if event.key in KEYS_PAUSE or event.key in KEYS_CANCEL:
                if audio_mgr:
                    audio_mgr.play_sfx("menu_cancel", "ui")
                self.sub_mode = "main"
            elif any(event.key == k for k in KEYS_UP):
                if audio_mgr:
                    audio_mgr.play_sfx("menu_move", "ui")
                self.settings_index = (self.settings_index - 1) % len(self.settings_options)
            elif any(event.key == k for k in KEYS_DOWN):
                if audio_mgr:
                    audio_mgr.play_sfx("menu_move", "ui")
                self.settings_index = (self.settings_index + 1) % len(self.settings_options)
            elif any(event.key == k for k in KEYS_LEFT):
                self._adjust_setting(self.settings_index, -1, audio_mgr, touch_ctrl)
            elif any(event.key == k for k in KEYS_RIGHT) or event.key in KEYS_INTERACT or event.key in KEYS_CONFIRM:
                if self.settings_options[self.settings_index] == "BACK":
                    if audio_mgr:
                        audio_mgr.play_sfx("menu_cancel", "ui")
                    self.sub_mode = "main"
                else:
                    self._adjust_setting(self.settings_index, 1, audio_mgr, touch_ctrl)

    def _adjust_setting(self, idx, direction, audio_mgr, touch_ctrl):
        setting = self.settings_options[idx]
        if setting == "Music" and audio_mgr:
            new_v = round(audio_mgr.music_volume + direction * 0.1, 1)
            audio_mgr.set_music_volume(max(0.0, min(1.0, new_v)))
            audio_mgr.play_sfx("menu_select", "ui")
        elif setting == "SFX" and audio_mgr:
            new_v = round(audio_mgr.sfx_volume + direction * 0.1, 1)
            audio_mgr.set_sfx_volume(max(0.0, min(1.0, new_v)))
            audio_mgr.play_sfx("menu_select", "ui")
        elif setting == "Mute" and audio_mgr:
            audio_mgr.toggle_music_mute()
            audio_mgr.toggle_sfx_mute()
            audio_mgr.play_sfx("menu_select", "ui")
        elif setting == "Touch" and touch_ctrl:
            modes = ["auto", "always", "hidden"]
            cur = modes.index(touch_ctrl.mode) if touch_ctrl.mode in modes else 0
            touch_ctrl.mode = modes[(cur + direction) % len(modes)]
            touch_ctrl.visible = (touch_ctrl.mode != "hidden")
            touch_ctrl.enabled = (touch_ctrl.mode != "hidden")
            if audio_mgr:
                audio_mgr.play_sfx("menu_select", "ui")
        elif setting == "T.Size" and touch_ctrl:
            sizes = ["normal", "large", "small"]
            cur = sizes.index(touch_ctrl.size_preset) if touch_ctrl.size_preset in sizes else 0
            touch_ctrl.set_size_preset(sizes[(cur + direction) % len(sizes)])
            if audio_mgr:
                audio_mgr.play_sfx("menu_select", "ui")
        elif setting == "T.Alpha" and touch_ctrl:
            alphas = [1.0, 0.75, 0.50]
            cur = 0
            for i, a in enumerate(alphas):
                if abs(touch_ctrl.opacity - a) < 0.12:
                    cur = i
                    break
            touch_ctrl.set_opacity(alphas[(cur + direction) % len(alphas)])
            if audio_mgr:
                audio_mgr.play_sfx("menu_select", "ui")

    def draw(self, surface, player=None, audio_mgr=None, touch_ctrl=None):
        overlay = pygame.Surface((GAME_W, GAME_H))
        overlay.fill(COLOR_LIGHTEST)
        overlay.set_alpha(190)
        surface.blit(overlay, (0, 0))

        self.ui.draw_box(surface, 18, 8, 124, 128)

        if self.sub_mode == "main":
            # Header
            self.ui.draw_text_centered(surface, "== PAUSED ==", 14, COLOR_DARKEST, font_heading())

            # Player HP Status Indicator
            if player:
                hp_str = f"HP {player.hp}/{player.max_hp}"
                self.ui.draw_text(surface, hp_str, 26, 28, COLOR_DARKEST, font_tag())
                self.ui.draw_hp_bar(surface, 78, 29, player.hp, player.max_hp)

            # Options
            start_y = 42
            for i, opt in enumerate(self.options):
                prefix = "> " if i == self.index else "  "
                color = COLOR_DARKEST if i == self.index else COLOR_DARK
                self.ui.draw_text(surface, prefix + opt, 26, start_y + i * 14, color, font_subheading())

        elif self.sub_mode == "settings":
            self.ui.draw_text_centered(surface, "= SETTINGS =", 13, COLOR_DARKEST, font_heading())

            m_vol = int((audio_mgr.music_volume if audio_mgr else 0.6) * 100)
            s_vol = int((audio_mgr.sfx_volume if audio_mgr else 0.7) * 100)
            is_mute = "YES" if (audio_mgr and audio_mgr.music_muted) else "NO"
            t_mode = (touch_ctrl.mode.upper() if touch_ctrl else "AUTO")
            t_size = (touch_ctrl.size_preset.upper() if touch_ctrl else "NORMAL")
            t_alpha = f"{int((touch_ctrl.opacity if touch_ctrl else 0.9) * 100)}%"

            lines = [
                f"Music: <{m_vol}%>",
                f"SFX:   <{s_vol}%>",
                f"Mute:  [{is_mute}]",
                f"Touch: [{t_mode}]",
                f"T.Size:[{t_size}]",
                f"Alpha: [{t_alpha}]",
                "BACK"
            ]

            start_y = 26
            for i, line in enumerate(lines):
                prefix = "> " if i == self.settings_index else "  "
                color = COLOR_DARKEST if i == self.settings_index else COLOR_DARK
                self.ui.draw_text(surface, prefix + line, 22, start_y + i * 13, color, font_subheading())

            self.ui.draw_text_centered(surface, "<- / -> Adjust", 120, COLOR_DARK, font_tag())


class InventoryScreen:
    """Categorized Inventory with actual 16x16 item icons and consumable usage."""
    CATEGORIES = ["Items", "Gear", "Keys"]

    def __init__(self, ui):
        self.ui = ui
        self.cat_index = 0
        self.item_index = 0
        self.done = False
        self.inventory = None
        self.items_in_cat = []
        self.on_use_item = None

    def open(self, inventory, on_use_item=None):
        self.inventory = inventory
        self.on_use_item = on_use_item
        self.item_index = 0
        self.done = False
        self._refresh()

    def _refresh(self):
        cat = self.CATEGORIES[self.cat_index]
        self.items_in_cat = self.inventory.get_by_category(cat)
        if self.items_in_cat:
            self.item_index = min(self.item_index, len(self.items_in_cat) - 1)
        else:
            self.item_index = 0

    def handle_event(self, event, audio_mgr=None):
        if event.type != pygame.KEYDOWN:
            return

        if event.key in KEYS_CANCEL or event.key in KEYS_PAUSE:
            if audio_mgr:
                audio_mgr.play_sfx("menu_cancel", "ui")
            self.done = True
        elif any(event.key == k for k in KEYS_LEFT):
            self.cat_index = (self.cat_index - 1) % len(self.CATEGORIES)
            self.item_index = 0
            self._refresh()
            if audio_mgr:
                audio_mgr.play_sfx("menu_move", "ui")
        elif any(event.key == k for k in KEYS_RIGHT):
            self.cat_index = (self.cat_index + 1) % len(self.CATEGORIES)
            self.item_index = 0
            self._refresh()
            if audio_mgr:
                audio_mgr.play_sfx("menu_move", "ui")
        elif any(event.key == k for k in KEYS_UP) and self.items_in_cat:
            self.item_index = (self.item_index - 1) % len(self.items_in_cat)
            if audio_mgr:
                audio_mgr.play_sfx("menu_move", "ui")
        elif any(event.key == k for k in KEYS_DOWN) and self.items_in_cat:
            self.item_index = (self.item_index + 1) % len(self.items_in_cat)
            if audio_mgr:
                audio_mgr.play_sfx("menu_move", "ui")
        elif event.key in KEYS_INTERACT or event.key in KEYS_CONFIRM:
            if self.items_in_cat and self.on_use_item:
                item, qty = self.items_in_cat[self.item_index]
                if audio_mgr:
                    audio_mgr.play_sfx("item_use", "items")
                self.on_use_item(item)
                self._refresh()

    def draw(self, surface, player=None):
        surface.fill(COLOR_LIGHTEST)
        self.ui.draw_box(surface, 2, 2, 156, 140)

        # Header Tabs (Press Start 2P)
        tab_x = 8
        for i, cat in enumerate(self.CATEGORIES):
            is_sel = (i == self.cat_index)
            color = COLOR_DARKEST if is_sel else COLOR_DARK
            marker = f"[{cat}]" if is_sel else f" {cat} "
            self.ui.draw_text(surface, marker, tab_x, 6, color, font_subheading())
            tab_x += 50

        pygame.draw.line(surface, COLOR_DARKEST, (4, 18), (154, 18))

        # Item List (Pixel Operator)
        if not self.items_in_cat:
            self.ui.draw_text(surface, "No items in this pocket.", 10, 30, COLOR_DARK, font_body())
        else:
            visible_start = max(0, self.item_index - 3)
            y = 22
            for i in range(visible_start, min(len(self.items_in_cat), visible_start + 4)):
                item, qty = self.items_in_cat[i]
                is_selected = (i == self.item_index)

                if is_selected:
                    self.ui.draw_box(surface, 4, y - 1, 152, 18, fill=COLOR_LIGHT, border=COLOR_DARKEST)

                # Real Item Icon
                icon = item.get_icon()
                surface.blit(icon, (8, y))

                # Name and quantity (Pixel Operator)
                name = item.name
                if qty > 1:
                    name += f" x{qty}"
                name_color = COLOR_DARKEST if is_selected else COLOR_DARK
                self.ui.draw_text(surface, name, 28, y + 1, name_color, font_body())
                y += 19

        # Bottom Detail / Inspection Panel
        self.ui.draw_box(surface, 4, 100, 152, 40)
        if self.items_in_cat:
            sel_item, sel_qty = self.items_in_cat[self.item_index]
            surface.blit(sel_item.get_icon(), (8, 104))
            # Item Name (Press Start 2P)
            self.ui.draw_text(surface, sel_item.name, 28, 104, COLOR_DARKEST, font_subheading())

            # Item Description (Pixel Operator)
            desc = sel_item.description
            if len(desc) > 30:
                d1 = desc[:30]
                d2 = desc[30:60]
                self.ui.draw_text(surface, d1, 28, 115, COLOR_DARK, font_body_small())
                self.ui.draw_text(surface, d2, 28, 126, COLOR_DARK, font_body_small())
            else:
                self.ui.draw_text(surface, desc, 28, 116, COLOR_DARK, font_body_small())

            # Action Hint (Press Start 2P)
            if sel_item.consumable:
                self.ui.draw_text(surface, "[USE]", 118, 104, COLOR_DARKEST, font_tag())
        else:
            self.ui.draw_text(surface, "Select a tab using Left/Right.", 8, 114, COLOR_DARK, font_body_small())


class QuestScreen:
    def __init__(self, ui):
        self.ui = ui
        self.index = 0
        self.done = False
        self.quests = []

    def open(self, quest_manager):
        self.quests = quest_manager.get_active()
        self.index = 0
        self.done = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in KEYS_CANCEL or event.key in KEYS_PAUSE:
            self.done = True
        elif any(event.key == k for k in KEYS_UP) and self.quests:
            self.index = (self.index - 1) % len(self.quests)
        elif any(event.key == k for k in KEYS_DOWN) and self.quests:
            self.index = (self.index + 1) % len(self.quests)

    def draw(self, surface):
        surface.fill(COLOR_LIGHTEST)
        self.ui.draw_box(surface, 2, 2, 156, 140)
        # Header (Press Start 2P)
        self.ui.draw_text(surface, "QUEST LOG", 8, 6, COLOR_DARKEST, font_heading())
        self.ui.draw_text(surface, "[X] Back", 102, 7, COLOR_DARK, font_tag())
        pygame.draw.line(surface, COLOR_DARKEST, (4, 18), (154, 18))

        if not self.quests:
            self.ui.draw_text(surface, "No active quests.", 10, 28, COLOR_DARK, font_body())
        else:
            y = 22
            for i, q in enumerate(self.quests):
                prefix = "> " if i == self.index else "  "
                status = " [OK]" if q.completed else ""
                color = COLOR_DARKEST if i == self.index else COLOR_DARK
                self.ui.draw_text(surface, f"{prefix}{q.title}{status}", 6, y, color, font_subheading())
                y += 14

            if self.quests:
                sel = self.quests[self.index]
                self.ui.draw_box(surface, 4, 90, 152, 48)
                # Header (Press Start 2P)
                self.ui.draw_text(surface, "CURRENT OBJECTIVE:", 8, 94, COLOR_DARKEST, font_tag())
                st = sel.stage_text()
                # Objective body (Pixel Operator)
                if len(st) > 28:
                    self.ui.draw_text(surface, st[:28], 8, 107, COLOR_DARK, font_body())
                    self.ui.draw_text(surface, st[28:56], 8, 120, COLOR_DARK, font_body())
                else:
                    self.ui.draw_text(surface, st, 8, 110, COLOR_DARK, font_body())


class TransitionEffect:
    def __init__(self):
        self.active = False
        self.phase = "none"
        self.timer = 0
        self.duration_out = 160
        self.duration_hold = 80
        self.duration_in = 160
        self.callback = None
        self.overlay = pygame.Surface((GAME_W, GAME_H))
        self.overlay.fill(COLOR_DARKEST)

    def start(self, callback=None):
        self.active = True
        self.phase = "out"
        self.timer = 0
        self.callback = callback

    def update(self, dt_ms):
        if not self.active:
            return
        self.timer += dt_ms
        if self.phase == "out" and self.timer >= self.duration_out:
            self.phase = "hold"
            self.timer = 0
            if self.callback:
                self.callback()
                self.callback = None
        elif self.phase == "hold" and self.timer >= self.duration_hold:
            self.phase = "in"
            self.timer = 0
        elif self.phase == "in" and self.timer >= self.duration_in:
            self.active = False
            self.phase = "none"

    def draw(self, surface):
        if not self.active:
            return
        if self.phase == "out":
            alpha = int(255 * (self.timer / self.duration_out))
        elif self.phase == "hold":
            alpha = 255
        elif self.phase == "in":
            alpha = int(255 * (1 - self.timer / self.duration_in))
        else:
            return
        self.overlay.set_alpha(min(255, max(0, alpha)))
        surface.blit(self.overlay, (0, 0))


class NotificationPopup:
    def __init__(self, ui):
        self.ui = ui
        self.text = ""
        self.timer = 0
        self.duration = 2000
        self.active = False

    def show(self, text, duration=2000):
        self.text = text
        self.timer = 0
        self.duration = duration
        self.active = True

    def update(self, dt_ms):
        if self.active:
            self.timer += dt_ms
            if self.timer >= self.duration:
                self.active = False

    def draw(self, surface):
        if not self.active:
            return
        # Use Press Start 2P tag font for popup
        f = font_tag()
        tw = f.size(self.text)[0]
        w = min(GAME_W - 8, tw + 12)
        x = (GAME_W - w) // 2
        self.ui.draw_box(surface, x, 3, w, 15)
        self.ui.draw_text_centered(surface, self.text, 6, COLOR_DARKEST, f)
