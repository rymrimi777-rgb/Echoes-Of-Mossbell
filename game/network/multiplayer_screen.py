"""
Game Mode Selection & Multiplayer Lobby UI Screens.
Designed for authentic 160x144 Game Boy resolution.
Supports keyboard, D-pad, and touch input (including on-screen keypad for mobile Room ID entry).
"""
import time
import pygame
from game.settings import (
    GAME_W, GAME_H, COLOR_DARKEST, COLOR_DARK, COLOR_LIGHT, COLOR_LIGHTEST,
    KEYS_UP, KEYS_DOWN, KEYS_LEFT, KEYS_RIGHT, KEYS_CONFIRM, KEYS_INTERACT, KEYS_CANCEL
)
from game.fonts import font_heading, font_subheading, font_tag, font_body_small, font_body
from game.character_registry import load_portrait, get_character
from game.network.room_manager import RoomManager


class GameModeScreen:
    """Screen presented after character selection to choose SOLO or PLAY WITH FRIENDS."""

    def __init__(self, ui):
        self.ui = ui
        self.options = ["SOLO", "PLAY WITH FRIENDS", "BACK"]
        self.index = 0
        self.done = False
        self.choice = None
        self.character_id = "actor1_character_01"

    def reset(self, character_id="actor1_character_01"):
        self.character_id = character_id
        self.index = 0
        self.done = False
        self.choice = None

    def handle_event(self, event, audio_mgr=None):
        if event.type == pygame.KEYDOWN:
            old = self.index
            if any(event.key == k for k in KEYS_UP):
                self.index = (self.index - 1) % len(self.options)
            elif any(event.key == k for k in KEYS_DOWN):
                self.index = (self.index + 1) % len(self.options)
            elif event.key in KEYS_CONFIRM or event.key in KEYS_INTERACT:
                if audio_mgr:
                    audio_mgr.play_sfx("menu_select", "ui")
                self.choice = self.options[self.index]
                self.done = True
                return
            elif event.key in KEYS_CANCEL:
                if audio_mgr:
                    audio_mgr.play_sfx("menu_cancel", "ui")
                self.choice = "BACK"
                self.done = True
                return

            if self.index != old and audio_mgr:
                audio_mgr.play_sfx("menu_move", "ui")

    def handle_pointer_down(self, native_x, native_y, audio_mgr=None):
        start_y = 66
        spacing = 18
        for i in range(len(self.options)):
            rect = pygame.Rect(20, start_y + i * spacing - 2, 120, 16)
            if rect.collidepoint(native_x, native_y):
                self.index = i
                if audio_mgr:
                    audio_mgr.play_sfx("menu_select", "ui")
                self.choice = self.options[i]
                self.done = True
                return True
        return False

    def update(self, dt_ms):
        pass

    def draw(self, surface):
        surface.fill(COLOR_LIGHTEST)

        # Header banner
        pygame.draw.rect(surface, COLOR_DARKEST, (0, 0, 160, 14))
        title = font_subheading().render("= SELECT MODE =", False, COLOR_LIGHTEST)
        surface.blit(title, ((160 - title.get_width()) // 2, 2))

        # Selected Hero Card
        char_info = get_character(self.character_id)
        card_rect = pygame.Rect(12, 20, 136, 32)
        pygame.draw.rect(surface, COLOR_LIGHT, card_rect)
        pygame.draw.rect(surface, COLOR_DARKEST, card_rect, 1)

        port = load_portrait(char_info, size=(24, 24))
        surface.blit(port, (16, 24))
        pygame.draw.rect(surface, COLOR_DARKEST, (15, 23, 26, 26), 1)

        f_body = font_body_small()
        surface.blit(font_subheading().render(char_info["name"].upper(), False, COLOR_DARKEST), (46, 22))
        surface.blit(f_body.render(char_info["title"], False, COLOR_DARK), (46, 34))

        # Options
        start_y = 66
        spacing = 18
        f_sub = font_subheading()
        for i, opt in enumerate(self.options):
            is_sel = (i == self.index)
            color = COLOR_DARKEST if is_sel else COLOR_DARK
            prefix = "> " if is_sel else "  "

            if is_sel:
                pygame.draw.rect(surface, COLOR_LIGHT, (20, start_y + i * spacing - 2, 120, 15))
                pygame.draw.rect(surface, COLOR_DARKEST, (20, start_y + i * spacing - 2, 120, 15), 1)

            opt_surf = f_sub.render(prefix + opt, False, color)
            surface.blit(opt_surf, (24, start_y + i * spacing))

        # Prompt
        prompt = font_tag().render("A: SELECT    B: BACK", False, COLOR_DARK)
        surface.blit(prompt, ((160 - prompt.get_width()) // 2, 128))


class MultiplayerLobbyScreen:
    """
    Complete 2-player pixel-art multiplayer lobby.
    Handles CREATE ROOM, JOIN ROOM, on-screen keypad input, and session waiting.
    """

    MODE_MAIN = "main"
    MODE_CREATE_WAIT = "create_wait"
    MODE_JOIN_INPUT = "join_input"
    MODE_CONNECTING = "connecting"

    def __init__(self, ui, room_manager: RoomManager):
        self.ui = ui
        self.room_mgr = room_manager
        self.character_id = "actor1_character_01"

        self.mode = self.MODE_MAIN
        self.main_options = ["CREATE ROOM", "JOIN ROOM", "BACK"]
        self.main_index = 0

        self.input_code = ""
        self.status_message = ""
        self.is_error = False

        self.blink_timer = 0
        self.blink_state = True
        self.poll_timer = 0

        self.session_ready = False
        self.done = False
        self.canceled = False

        # Virtual keypad hitboxes (0-9, DEL, OK)
        self.keypad_rects = {}
        self._init_keypad()

    def _init_keypad(self):
        # 3 rows x 4 cols keypad for touch screen
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "DEL", "OK"]
        start_x = 20
        start_y = 66
        w, h = 28, 14
        for idx, k in enumerate(keys):
            row = idx // 4
            col = idx % 4
            x = start_x + col * (w + 2)
            y = start_y + row * (h + 2)
            self.keypad_rects[k] = pygame.Rect(x, y, w, h)

    def reset(self, character_id="actor1_character_01"):
        self.character_id = character_id
        self.mode = self.MODE_MAIN
        self.main_index = 0
        self.input_code = ""
        self.status_message = ""
        self.is_error = False
        self.session_ready = False
        self.done = False
        self.canceled = False
        self.poll_timer = 0

    def handle_event(self, event, audio_mgr=None):
        if self.mode == self.MODE_MAIN:
            self._handle_main_event(event, audio_mgr)
        elif self.mode == self.MODE_CREATE_WAIT:
            self._handle_create_wait_event(event, audio_mgr)
        elif self.mode == self.MODE_JOIN_INPUT:
            self._handle_join_input_event(event, audio_mgr)

    def _handle_main_event(self, event, audio_mgr):
        if event.type != pygame.KEYDOWN:
            return
        old = self.main_index
        if any(event.key == k for k in KEYS_UP):
            self.main_index = (self.main_index - 1) % len(self.main_options)
        elif any(event.key == k for k in KEYS_DOWN):
            self.main_index = (self.main_index + 1) % len(self.main_options)
        elif event.key in KEYS_CONFIRM or event.key in KEYS_INTERACT:
            choice = self.main_options[self.main_index]
            if choice == "CREATE ROOM":
                self._start_create_room(audio_mgr)
            elif choice == "JOIN ROOM":
                self.mode = self.MODE_JOIN_INPUT
                self.input_code = ""
                self.status_message = ""
                self.is_error = False
                if audio_mgr:
                    audio_mgr.play_sfx("menu_select", "ui")
            elif choice == "BACK":
                self.canceled = True
                self.done = True
                if audio_mgr:
                    audio_mgr.play_sfx("menu_cancel", "ui")
            return
        elif event.key in KEYS_CANCEL:
            self.canceled = True
            self.done = True
            if audio_mgr:
                audio_mgr.play_sfx("menu_cancel", "ui")
            return

        if self.main_index != old and audio_mgr:
            audio_mgr.play_sfx("menu_move", "ui")

    def _handle_create_wait_event(self, event, audio_mgr):
        if event.type == pygame.KEYDOWN and event.key in KEYS_CANCEL:
            self.room_mgr.leave_room()
            self.mode = self.MODE_MAIN
            if audio_mgr:
                audio_mgr.play_sfx("menu_cancel", "ui")

    def _handle_join_input_event(self, event, audio_mgr):
        if event.type != pygame.KEYDOWN:
            return

        # Backspace edits the input code
        if event.key == pygame.K_BACKSPACE:
            if self.input_code:
                self.input_code = self.input_code[:-1]
                if audio_mgr:
                    audio_mgr.play_sfx("menu_move", "ui")
            return

        if event.key in (pygame.K_ESCAPE, pygame.K_x):
            self.mode = self.MODE_MAIN
            if audio_mgr:
                audio_mgr.play_sfx("menu_cancel", "ui")
            return

        # Digits 0-9
        if pygame.K_0 <= event.key <= pygame.K_9 or pygame.K_KP0 <= event.key <= pygame.K_KP9:
            digit = event.unicode if event.unicode.isdigit() else str((event.key - pygame.K_0) % 10)
            if len(self.input_code) < 5:
                self.input_code += digit
                if audio_mgr:
                    audio_mgr.play_sfx("menu_move", "ui")

        elif event.key in KEYS_CONFIRM or event.key in KEYS_INTERACT:
            if len(self.input_code) >= 4:
                self._attempt_join_room(self.input_code, audio_mgr)
            else:
                self.status_message = "Enter 5-digit code!"
                self.is_error = True

    def handle_pointer_down(self, native_x, native_y, audio_mgr=None):
        if self.mode == self.MODE_MAIN:
            start_y = 66
            spacing = 18
            for i, opt in enumerate(self.main_options):
                r = pygame.Rect(20, start_y + i * spacing - 2, 120, 16)
                if r.collidepoint(native_x, native_y):
                    self.main_index = i
                    if opt == "CREATE ROOM":
                        self._start_create_room(audio_mgr)
                    elif opt == "JOIN ROOM":
                        self.mode = self.MODE_JOIN_INPUT
                        self.input_code = ""
                        self.status_message = ""
                        self.is_error = False
                    elif opt == "BACK":
                        self.canceled = True
                        self.done = True
                    return True

        elif self.mode == self.MODE_CREATE_WAIT:
            btn = pygame.Rect(40, 120, 80, 16)
            if btn.collidepoint(native_x, native_y):
                self.room_mgr.leave_room()
                self.mode = self.MODE_MAIN
                return True

        elif self.mode == self.MODE_JOIN_INPUT:
            # Keypad touches
            for k, rect in self.keypad_rects.items():
                if rect.collidepoint(native_x, native_y):
                    if k == "DEL":
                        if self.input_code:
                            self.input_code = self.input_code[:-1]
                    elif k == "OK":
                        if len(self.input_code) >= 4:
                            self._attempt_join_room(self.input_code, audio_mgr)
                        else:
                            self.status_message = "Enter 5-digit code!"
                            self.is_error = True
                    else:
                        if len(self.input_code) < 5:
                            self.input_code += k
                    return True

            cancel_btn = pygame.Rect(40, 126, 80, 14)
            if cancel_btn.collidepoint(native_x, native_y):
                self.mode = self.MODE_MAIN
                return True

        return False

    def _start_create_room(self, audio_mgr):
        char_name = get_character(self.character_id)["name"]
        ok, room_id = self.room_mgr.create_room(self.character_id, player_name=char_name)
        if ok:
            self.mode = self.MODE_CREATE_WAIT
            self.status_message = "Waiting for Player 2..."
            self.is_error = False
            if audio_mgr:
                audio_mgr.play_sfx("menu_select", "ui")
        else:
            self.status_message = f"Error: {room_id}"
            self.is_error = True

    def _attempt_join_room(self, code, audio_mgr):
        char_name = get_character(self.character_id)["name"]
        ok, res = self.room_mgr.join_room(code, self.character_id, player_name=char_name)
        if ok:
            if audio_mgr:
                audio_mgr.play_sfx("menu_select", "ui")
            self.session_ready = True
            self.done = True
        else:
            self.is_error = True
            if res == "ROOM_FULL":
                self.status_message = "Room is full! (2/2)"
            elif res == "ROOM_NOT_FOUND":
                self.status_message = "Room not found!"
            elif res == "ROOM_CLOSED":
                self.status_message = "Room is closed!"
            elif res == "HOST_DISCONNECTED":
                self.status_message = "Host disconnected!"
            else:
                self.status_message = f"Failed: {res}"

    def update(self, dt_ms):
        self.blink_timer += dt_ms
        if self.blink_timer >= 350:
            self.blink_timer -= 350
            self.blink_state = not self.blink_state

        if self.mode == self.MODE_CREATE_WAIT:
            # Poll every 400ms to check if player 2 joined
            self.poll_timer += dt_ms
            if self.poll_timer >= 400:
                self.poll_timer = 0
                has_p2, _ = self.room_mgr.poll_waiting_room()
                if has_p2:
                    self.session_ready = True
                    self.done = True

    def draw(self, surface):
        surface.fill(COLOR_LIGHTEST)

        # Header
        pygame.draw.rect(surface, COLOR_DARKEST, (0, 0, 160, 14))
        title = font_subheading().render("= MULTIPLAYER LOBBY =", False, COLOR_LIGHTEST)
        surface.blit(title, ((160 - title.get_width()) // 2, 2))

        if self.mode == self.MODE_MAIN:
            self._draw_main(surface)
        elif self.mode == self.MODE_CREATE_WAIT:
            self._draw_create_wait(surface)
        elif self.mode == self.MODE_JOIN_INPUT:
            self._draw_join_input(surface)

    def _draw_main(self, surface):
        # Character summary
        char_info = get_character(self.character_id)
        card_rect = pygame.Rect(12, 20, 136, 32)
        pygame.draw.rect(surface, COLOR_LIGHT, card_rect)
        pygame.draw.rect(surface, COLOR_DARKEST, card_rect, 1)

        port = load_portrait(char_info, size=(24, 24))
        surface.blit(port, (16, 24))
        pygame.draw.rect(surface, COLOR_DARKEST, (15, 23, 26, 26), 1)

        surface.blit(font_subheading().render(char_info["name"].upper(), False, COLOR_DARKEST), (46, 22))
        surface.blit(font_body_small().render("Online 2-Player Co-op", False, COLOR_DARK), (46, 34))

        start_y = 66
        spacing = 18
        f_sub = font_subheading()
        for i, opt in enumerate(self.main_options):
            is_sel = (i == self.main_index)
            color = COLOR_DARKEST if is_sel else COLOR_DARK
            prefix = "> " if is_sel else "  "

            if is_sel:
                pygame.draw.rect(surface, COLOR_LIGHT, (20, start_y + i * spacing - 2, 120, 15))
                pygame.draw.rect(surface, COLOR_DARKEST, (20, start_y + i * spacing - 2, 120, 15), 1)

            surface.blit(f_sub.render(prefix + opt, False, color), (24, start_y + i * spacing))

        prompt = font_tag().render("A: SELECT    B: BACK", False, COLOR_DARK)
        surface.blit(prompt, ((160 - prompt.get_width()) // 2, 128))

    def _draw_create_wait(self, surface):
        rid = self.room_mgr.current_room_id or "....."

        # Room Code Box
        box_rect = pygame.Rect(16, 22, 128, 44)
        pygame.draw.rect(surface, COLOR_LIGHT, box_rect)
        pygame.draw.rect(surface, COLOR_DARKEST, box_rect, 2)

        surface.blit(font_tag().render("SHARE THIS ROOM CODE:", False, COLOR_DARK), (22, 26))

        code_surf = font_heading().render(f"  {rid}  ", False, COLOR_DARKEST)
        surface.blit(code_surf, ((160 - code_surf.get_width()) // 2, 38))

        # Waiting indicator
        dots = "." * (int(time.time() * 2) % 4)
        wait_text = f"Waiting for 2P{dots}"
        surface.blit(font_body().render(wait_text, False, COLOR_DARKEST), (30, 78))

        # Player slots status
        char_info = get_character(self.character_id)
        p1_str = f"[1P] {char_info['name']} (Host Ready)"
        p2_str = "[2P] Waiting to connect..."
        surface.blit(font_tag().render(p1_str, False, COLOR_DARK), (22, 94))
        surface.blit(font_tag().render(p2_str, False, COLOR_DARKEST), (22, 105))

        # Cancel button
        cancel_rect = pygame.Rect(40, 122, 80, 15)
        pygame.draw.rect(surface, COLOR_DARK, cancel_rect)
        cancel_txt = font_tag().render("B: CANCEL", False, COLOR_LIGHTEST)
        surface.blit(cancel_txt, ((160 - cancel_txt.get_width()) // 2, 124))

    def _draw_join_input(self, surface):
        # Room input display
        box = pygame.Rect(20, 20, 120, 24)
        pygame.draw.rect(surface, COLOR_LIGHT, box)
        pygame.draw.rect(surface, COLOR_DARKEST, box, 1)

        display_text = self.input_code
        if self.blink_state:
            display_text += "_"

        surface.blit(font_tag().render("ROOM CODE (5 Digits):", False, COLOR_DARK), (22, 16))
        code_s = font_heading().render(display_text, False, COLOR_DARKEST)
        surface.blit(code_s, (26, 27))

        if self.status_message:
            color = COLOR_DARKEST if not self.is_error else (15, 56, 15)
            surface.blit(font_tag().render(self.status_message, False, color), (22, 48))

        # Virtual keypad for touch / visual reference
        f_tag = font_tag()
        for k, rect in self.keypad_rects.items():
            is_ok = (k == "OK")
            is_del = (k == "DEL")
            bg = COLOR_DARKEST if is_ok else (COLOR_DARK if is_del else COLOR_LIGHT)
            fg = COLOR_LIGHTEST if (is_ok or is_del) else COLOR_DARKEST

            pygame.draw.rect(surface, bg, rect)
            pygame.draw.rect(surface, COLOR_DARKEST, rect, 1)
            t = f_tag.render(k, False, fg)
            surface.blit(t, (rect.x + (rect.w - t.get_width()) // 2, rect.y + 2))

        # Cancel button
        cancel_rect = pygame.Rect(40, 126, 80, 14)
        pygame.draw.rect(surface, COLOR_DARK, cancel_rect)
        c_txt = f_tag.render("B: BACK", False, COLOR_LIGHTEST)
        surface.blit(c_txt, ((160 - c_txt.get_width()) // 2, 128))
