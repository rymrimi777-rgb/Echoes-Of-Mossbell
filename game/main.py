"""
Echoes of Mossbell – A Retro Handheld RPG
Main Game Engine, State Machine, Map Transitions, and Enhanced Input Integration.
"""
import pygame, sys, os, time, asyncio, math

# Ensure project root is in sys.path
if getattr(sys, "frozen", False):
    _root = os.path.dirname(sys.executable)
else:
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from game.settings import *
from game.player import Player
from game.camera import Camera
from game.animation import CharacterAnimator
from game.ocean_animator import OceanCharacterAnimator
from game.dialogue import DialogueBox
from game.inventory import Inventory, ITEMS
from game.quests import QuestManager
from game.audio import AudioManager
from game.save_system import SaveSystem
from game.ui import (UIRenderer, TitleScreen, PauseMenu, InventoryScreen,
                     QuestScreen, TransitionEffect, NotificationPopup)
from game.character_select import CharacterSelectScreen
from game.character_registry import get_character, get_default_character_id
from game.network import (
    FirebaseAuth, FirebaseClient, RoomManager, NetworkWorker,
    RemotePlayer, GameModeScreen, MultiplayerLobbyScreen
)
from game.touch_controls import TouchController
from game.fonts import font_tag
from game.map_loader import update_tile_animators
from game.world import build_all_maps

# States
STATE_TITLE       = "title"
STATE_CHAR_SELECT = "char_select"
STATE_GAME_MODE   = "game_mode"
STATE_MP_LOBBY    = "mp_lobby"
STATE_PLAY        = "play"
STATE_PAUSE       = "pause"
STATE_DIALOGUE    = "dialogue"
STATE_INVENTORY   = "inventory"
STATE_QUESTS      = "quests"
STATE_TRANSITION  = "transition"


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Echoes of Mossbell")

        icon_path = os.path.join(ASSET_DIR, "icon", "window_icon.png")
        if os.path.isfile(icon_path):
            try:
                pygame.display.set_icon(pygame.image.load(icon_path))
            except Exception:
                pass

        disp_flags = pygame.RESIZABLE
        if getattr(pygame, "IS_ANDROID", False) or IS_ANDROID:
            try:
                disp_flags |= pygame.FULLSCREEN
            except Exception:
                pass
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), disp_flags)
        self.native = pygame.Surface((GAME_W, GAME_H))
        self.clock = pygame.time.Clock()

        # Touch Controls (Auto on mobile / Resizable on desktop)
        scr_w, scr_h = self.screen.get_size()
        self.touch_ctrl = TouchController(scr_w, scr_h)
        if IS_ANDROID:
            self.touch_ctrl.mode = "always"
            self.touch_ctrl.visible = True

        # Core Systems
        self.ui = UIRenderer()
        self.audio = AudioManager()
        self.save_sys = SaveSystem()
        self.dialogue = DialogueBox()
        self.inventory = Inventory()
        self.quest_mgr = QuestManager()
        self.transition = TransitionEffect()
        self.notification = NotificationPopup(self.ui)
        self.pause_menu = PauseMenu(self.ui)
        self.inv_screen = InventoryScreen(self.ui)
        self.quest_screen = QuestScreen(self.ui)

        # World Maps
        self.maps = build_all_maps()
        self.current_map_id = "village"
        self.current_map = self.maps[self.current_map_id]

        # Player & Camera (Restores previously selected character)
        saved_char = self.save_sys.get_selected_character()
        self.player = Player(10 * TILE_SIZE, 9 * TILE_SIZE, character_id=saved_char)
        self.camera = Camera(self.current_map.width, self.current_map.height)

        # Character Selection Screen
        self.char_select = CharacterSelectScreen(self.ui, initial_char_id=saved_char)
        self.char_select_origin = "new_game"
        self.view_scale = 1.0
        self.view_offset = (0, 0)
        self._update_viewport_metrics()

        # Multiplayer & Network Systems
        self.firebase_auth = FirebaseAuth()
        self.firebase_client = FirebaseClient(self.firebase_auth)
        self.room_mgr = RoomManager(self.firebase_client)
        self.game_mode_screen = GameModeScreen(self.ui)
        self.mp_lobby_screen = MultiplayerLobbyScreen(self.ui, self.room_mgr)

        self.is_multiplayer = False
        self.network_worker = None
        self.remote_player = None

        # NPC Animators
        self.npc_animators = {}
        self._load_npc_animators()

        # Flags & Timing
        self.flags = {}
        self.play_time = 0.0
        self.interact_cooldown = 0

        # State
        self.state = STATE_TITLE
        self.title_screen = TitleScreen(self.ui, save_exists=self.save_sys.exists())
        self.running = True

        self.audio.play_music("stg01 - Title Screen.mp3")

    def _start_multiplayer_session(self):
        """Starts an active online 2-player multiplayer session."""
        self.is_multiplayer = True
        rid = self.room_mgr.current_room_id
        local_slot = self.room_mgr.local_slot
        remote_slot = self.room_mgr.remote_slot
        rem_info = self.room_mgr.remote_player_info or {}

        rem_char = rem_info.get("character_id", "actor1_character_02")
        rem_name = rem_info.get("name", "Player 2" if local_slot == "p1" else "Player 1")
        rem_x = float(rem_info.get("x", 176.0 if local_slot == "p1" else 160.0))
        rem_y = float(rem_info.get("y", 144.0))

        # Start solo-style world
        self._new_game(character_id=self.player.character_id)
        if local_slot == "p2":
            self.player.fx = 176.0
            self.player.x = 176

        # Initialize Remote Player
        self.remote_player = RemotePlayer(
            character_id=rem_char,
            name=rem_name,
            slot=remote_slot,
            x=rem_x,
            y=rem_y
        )

        # Launch background network worker thread
        self.network_worker = NetworkWorker(
            self.firebase_client,
            room_id=rid,
            local_slot=local_slot,
            remote_slot=remote_slot
        )
        self.network_worker.start()

        self.state = STATE_PLAY
        self.notification.show(f"Online Room {rid} Active! Joined as {local_slot.upper()}")
        self.audio.play_sfx("menu_select", "ui")

    def _stop_multiplayer(self):
        """Cleanly ends a multiplayer session and stops the worker thread."""
        if self.is_multiplayer:
            if self.network_worker:
                self.network_worker.stop()
                self.network_worker = None
            self.room_mgr.leave_room()
            self.remote_player = None
            self.is_multiplayer = False

    def _update_viewport_metrics(self):
        scr_w, scr_h = self.screen.get_size()
        scale = min(scr_w / GAME_W, scr_h / GAME_H)
        view_w = int(GAME_W * scale)
        view_h = int(GAME_H * scale)
        view_x = (scr_w - view_w) // 2
        view_y = 0 if scr_h > (scr_w * 1.1) else (scr_h - view_h) // 2
        self.view_scale = scale
        self.view_offset = (view_x, view_y)

    def _get_pointer_pos(self, event):
        """Returns screen (wx, wy) for desktop mouse left click or mobile FINGERDOWN."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not getattr(event, "touch", False):
            return event.pos
        if event.type == pygame.FINGERDOWN:
            scr_w, scr_h = self.screen.get_size()
            return int(event.x * scr_w), int(event.y * scr_h)
        return None

    def window_to_native(self, wx, wy):
        """Converts window/screen pixel coordinates to native 160x144 Game Boy space."""
        vx, vy = self.view_offset
        if self.view_scale <= 0:
            return 0, 0
        nx = int((wx - vx) / self.view_scale)
        ny = int((wy - vy) / self.view_scale)
        return max(0, min(GAME_W - 1, nx)), max(0, min(GAME_H - 1, ny))

    def _load_npc_animators(self):
        self.npc_animators = {}
        for npc in self.current_map.npcs:
            if npc.npc_id not in self.npc_animators:
                char_id = getattr(npc, "ocean_char_id", None)
                if not char_id:
                    legacy_map = {
                        "old_man.png": "actor1_character_05",
                        "boy.png": "actor1_character_02",
                        "king.png": "actor3_character_08",
                        "hero.png": "actor1_character_01",
                    }
                    char_id = legacy_map.get(getattr(npc, "sprite_file", ""), "actor1_character_01")
                variant = getattr(npc, "variant", "gameboy")
                anim = OceanCharacterAnimator(char_id, variant=variant, target_size=(24, 32), fps=8)
                anim.face(npc.direction)
                self.npc_animators[npc.npc_id] = anim

    def change_map(self, map_id, px, py):
        self.current_map_id = map_id
        self.current_map = self.maps[map_id]
        self.camera = Camera(self.current_map.width, self.current_map.height)
        self.player.fx = float(px)
        self.player.fy = float(py)
        self.player.x = int(px)
        self.player.y = int(py)
        self.player.moving = False
        self._load_npc_animators()

        if self.current_map.music:
            self.audio.play_music(self.current_map.music)

    def _do_warp(self, warp):
        def apply():
            self.change_map(warp.target_map, warp.target_x, warp.target_y)
        self.transition.start(apply)
        self.state = STATE_TRANSITION
        self.player.moving = False
        self.audio.play_sfx("door_open", "environment")

    # ---- Proximity & Interaction -------------------------------------------
    def _get_nearby_target(self):
        """Returns any NPC, interactive object, or item pickup within interaction reach."""
        for npc in self.current_map.npcs:
            if self.player.is_near_target(npc.rect):
                return ("npc", npc)
        for obj in self.current_map.interactives:
            if self.player.is_near_target(obj.rect):
                return ("obj", obj)
        for item in self.current_map.items:
            if item.flag_id and self.flags.get(item.flag_id):
                continue
            if self.player.is_near_target(item.rect):
                return ("item", item)
        return None

    def _interact(self):
        target = self._get_nearby_target()
        if target:
            kind, entity = target
            if kind == "npc":
                self._talk_to_npc(entity)
            elif kind == "obj":
                self._examine_object(entity)
            elif kind == "item":
                self._pickup_item(entity)
        else:
            self._player_attack()

    def _player_attack(self):
        swung = self.player.attack()
        if not swung:
            return

        self.audio.play_sfx("sword_swing.wav", "combat")
        atk_rect = self.player.get_attack_rect()

        if hasattr(self.current_map, "enemies"):
            for enemy in list(self.current_map.enemies):
                if enemy.is_alive and enemy.hit_rect.colliderect(atk_rect):
                    ex = enemy.x + enemy.fw // 2
                    ey = enemy.y + enemy.fh // 2
                    px, py = self.player.center_x, self.player.center_y
                    dist = max(1.0, math.hypot(ex - px, ey - py))
                    k_dir = ((ex - px) / dist, (ey - py) / dist)

                    dmg = 4 if self.inventory.has("sword") else 2
                    killed = enemy.take_damage(dmg, k_dir)
                    self.audio.play_sfx("hit_enemy.wav", "combat")

                    if killed:
                        self.notification.show(f"Defeated {enemy.name}!")
                        if enemy.loot:
                            self.inventory.add(enemy.loot, 1)
                            self.notification.show(f"Obtained {enemy.loot}!")
                            self.audio.play_sfx("item_pickup", "items")
                        if getattr(enemy, "ai_type", "") == "boss":
                            self.audio.play_sfx("boss_roar.wav", "combat")
                            self.notification.show("The Slime Sovereign has fallen!")
                            self.flags["boss_defeated"] = True
                            if not self.inventory.has("sun_amulet"):
                                self.inventory.add("sun_amulet", 1)

    def _handle_player_faint(self):
        self.notification.show("You collapsed! Restored to safety at home.")
        self.audio.play_sfx("door_open", "environment")
        self.player.hp = self.player.max_hp // 2
        self.change_map("player_house", 5 * TILE_SIZE, 5 * TILE_SIZE)

    def _examine_object(self, obj):
        self.audio.play_sfx("menu_select", "ui")
        self.player.moving = False

        if obj.on_interact == "heal_player":
            healed = self.player.heal(self.player.max_hp)
            if healed > 0:
                self.notification.show("Rested in bed! HP fully restored.")
                self.audio.play_sfx("heal", "player")

        self.dialogue.start(obj.dialogues, callback=self._on_dialogue_end)
        self.state = STATE_DIALOGUE

    def _talk_to_npc(self, npc):
        self.audio.play_sfx("greeting", "npc")
        self.player.moving = False

        anim = self.npc_animators.get(npc.npc_id)
        if anim:
            opp_dir = {"up": "down", "down": "up", "left": "right", "right": "left"}.get(self.player.direction, "down")
            if hasattr(anim, "face"):
                anim.face(opp_dir)
            else:
                anim.direction = opp_dir

        lines = self._get_quest_dialogue(npc)
        if not lines:
            lines = list(npc.dialogues) if npc.dialogues else ["..."]

        self.dialogue.start(lines, callback=lambda: self._on_dialogue_end(npc))
        self.state = STATE_DIALOGUE

    def _get_quest_dialogue(self, npc):
        if npc.npc_id == "elder":
            if self.quest_mgr.is_at_stage("main", 0):
                self.quest_mgr.advance("main")
                return [
                    {"text": "Welcome, child. Dark times have come to Mossbell.", "portrait": "old_man"},
                    {"text": "People vanish at night. The woods whisper strange things.", "portrait": "old_man"},
                    {"text": "Search Whispering Woods east of the village. Find what lurks there.", "portrait": "old_man"},
                ]
            elif self.quest_mgr.is_at_stage("main", 4):
                if self.inventory.has("crystal"):
                    self.quest_mgr.advance("main")
                    self.inventory.remove("crystal")
                    return [
                        {"text": "The Shadow Crystal! You found it in the deep forest!", "portrait": "old_man"},
                        {"text": "There is a hidden grotto beyond the dead trees...", "portrait": "old_man"},
                        {"text": "Confront the shadow entity there to banish this darkness forever!", "portrait": "old_man"},
                    ]
            elif self.quest_mgr.is_completed("main"):
                return [
                    {"text": "The darkness has lifted! The villagers have all returned safely.", "portrait": "old_man"},
                    {"text": "You are the true savior of Mossbell!", "portrait": "old_man"},
                ]
            return None

        elif npc.npc_id == "healer":
            if self.quest_mgr.is_at_stage("herbs", 0):
                self.quest_mgr.advance("herbs")
                return [
                    {"text": "Greetings! I tend to the sick, but my medicinal herbs are gone.", "portrait": "king"},
                    {"text": "If you find 3 Forest Herbs in Whispering Woods, bring them to me.", "portrait": "king"},
                ]
            elif self.quest_mgr.is_at_stage("herbs", 1):
                if self.inventory.has("herb", 3):
                    self.inventory.remove("herb", 3)
                    self.quest_mgr.advance("herbs")
                    self.notification.show("Quest Complete: Herbal Remedy!")
                    self.inventory.add("potion", 2)
                    self.audio.play_sfx("SE - Get Point.mp3")
                    return [
                        {"text": "Splendid! These herbs will brew potent remedies.", "portrait": "king"},
                        {"text": "Please take these 2 Healing Potions for your journey!", "portrait": "king"},
                    ]
                else:
                    return [
                        {"text": "I still need 3 Forest Herbs. Search among the trees in the woods.", "portrait": "king"},
                    ]
            elif self.quest_mgr.is_completed("herbs"):
                return [
                    {"text": "Thank you again for the herbs! My patients are healing nicely.", "portrait": "king"},
                ]
            return None

        elif npc.npc_id == "boy":
            if self.quest_mgr.is_at_stage("ring", 0):
                self.quest_mgr.advance("ring")
                return [
                    {"text": "I lost my mother's silver ring near the old watchtower ruins...", "portrait": "boy"},
                    {"text": "It is the only keepsake I have left of her.", "portrait": "boy"},
                ]
            elif self.quest_mgr.is_at_stage("ring", 1):
                if self.inventory.has("ring"):
                    self.inventory.remove("ring")
                    self.quest_mgr.advance("ring")
                    self.notification.show("Quest Complete: The Lost Ring!")
                    self.inventory.add("apple", 2)
                    self.audio.play_sfx("SE - Get Point.mp3")
                    return [
                        {"text": "My mother's ring! You actually found it!", "portrait": "boy"},
                        {"text": "Thank you so much! Please take these sweet apples I picked!", "portrait": "boy"},
                    ]
                else:
                    return [
                        {"text": "Please look around the watchtower ruins to the south...", "portrait": "boy"},
                    ]
            elif self.quest_mgr.is_completed("ring"):
                return [
                    {"text": "I will cherish this ring forever. Thank you, hero!", "portrait": "boy"},
                ]
            return None

        elif npc.npc_id == "shadow":
            if self.quest_mgr.is_at_stage("main", 5):
                self.quest_mgr.advance("main")
                self.notification.show("The curse is broken! You saved Mossbell!")
                self.audio.play_sfx("SE - Target Destroyed.mp3")
                return [
                    {"text": "The crystal shatters the darkness that bound me...", "portrait": "king"},
                    {"text": "The vanished villagers are restored to the sunlight.", "portrait": "king"},
                    {"text": "The ancient curse is broken. Peace returns to Mossbell.", "portrait": "king"},
                    {"text": "Thank you, noble hero!", "portrait": "king"},
                ]
            return None

        return None

    def _on_dialogue_end(self, npc=None):
        self.state = STATE_PLAY
        self.interact_cooldown = 150

        if npc and hasattr(npc, "npc_id"):
            if npc.npc_id == "elder" and self.quest_mgr.is_at_stage("main", 1):
                self.notification.show("Quest: The Vanishing started!")
                self.audio.play_sfx("quest_start", "npc")
            elif npc.npc_id == "woodsman" and self.quest_mgr.is_at_stage("main", 1):
                self.quest_mgr.advance("main")
                self.notification.show("The deep woods hold the key...")
                self.audio.play_sfx("quest_start", "npc")

    def _pickup_item(self, item_pickup):
        self.inventory.add(item_pickup.item_id)
        if item_pickup.flag_id:
            self.flags[item_pickup.flag_id] = True

        name = ITEMS[item_pickup.item_id].name if item_pickup.item_id in ITEMS else item_pickup.item_id
        self.notification.show(f"Found {name}!")
        self.audio.play_sfx("item_pickup", "items")

        if item_pickup.item_id == "crystal":
            if self.quest_mgr.is_at_stage("main", 2) or self.quest_mgr.is_at_stage("main", 3):
                while not self.quest_mgr.is_at_stage("main", 4) and not self.quest_mgr.is_completed("main"):
                    self.quest_mgr.advance("main")
                self.notification.show("Bring the Shadow Crystal to Elder Orin!")
                self.audio.play_sfx("quest_start", "npc")

    def _use_inventory_item(self, item):
        if item.consumable and item.heal > 0:
            if self.player.hp >= self.player.max_hp:
                self.notification.show("Health is already full!")
            else:
                healed = self.player.heal(item.heal)
                self.inventory.remove(item.item_id, 1)
                self.audio.play_sfx("item_use", "items")
                self.notification.show(f"Used {item.name}! +{healed} HP")
        else:
            self.notification.show(f"{item.name}: {item.description}")

    # ---- Save / Load -------------------------------------------------------
    def _save_game(self):
        state = {
            "player_x": self.player.x,
            "player_y": self.player.y,
            "player_dir": self.player.direction,
            "player_hp": self.player.hp,
            "character_id": self.player.character_id,
            "variant": self.player.variant,
            "current_map": self.current_map_id,
            "inventory": self.inventory.to_dict(),
            "quests": self.quest_mgr.to_dict(),
            "flags": self.flags,
            "play_time": self.play_time,
        }
        self.save_sys.save(state)
        self.notification.show("Game saved successfully!")
        self.audio.play_sfx("menu_select", "ui")

    def _load_game(self):
        data = self.save_sys.load()
        if not data:
            return False
        char_id = data.get("character_id") or self.save_sys.get_selected_character()
        self.player.set_character(char_id, variant=data.get("variant", "gameboy"))
        self.char_select.set_by_id(char_id)
        self.change_map(data.get("current_map", "village"), data.get("player_x", 160), data.get("player_y", 144))
        self.player.direction = data.get("player_dir", "down")
        self.player.hp = data.get("player_hp", 20)
        self.inventory.from_dict(data.get("inventory", {}))
        self.quest_mgr.from_dict(data.get("quests", {}))
        self.flags = data.get("flags", {})
        self.play_time = data.get("play_time", 0)
        return True

    def _new_game(self, character_id=None):
        self.inventory = Inventory()
        self.inventory.add("bread", 1)
        self.quest_mgr = QuestManager()
        self.flags = {}
        self.play_time = 0.0
        self.change_map("village", 10 * TILE_SIZE, 9 * TILE_SIZE)
        char_id = character_id or self.save_sys.get_selected_character()
        self.player = Player(10 * TILE_SIZE, 9 * TILE_SIZE, character_id=char_id)
        self.char_select.set_by_id(char_id)
        self.quest_mgr.start("main")
        self.quest_mgr.start("herbs")
        self.quest_mgr.start("ring")

    # ---- Main Loop ---------------------------------------------------------
    async def run(self):
        while self.running:
            dt_ms = self.clock.tick(FPS)
            if dt_ms > 50:
                dt_ms = 50

            self._handle_events()
            self._update(dt_ms)
            self._draw()
            await asyncio.sleep(0)

        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._stop_multiplayer()
                self.running = False
                return

            # Android Lifecycle Events
            if hasattr(pygame, "APP_WILLENTERBACKGROUND") and event.type == pygame.APP_WILLENTERBACKGROUND:
                self.audio.pause_music()
                self._save_game()
            elif hasattr(pygame, "APP_DIDENTERFOREGROUND") and event.type == pygame.APP_DIDENTERFOREGROUND:
                self.audio.unpause_music()

            # Window Resize
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.touch_ctrl.update_layout(event.w, event.h)
                self._update_viewport_metrics()

            # Route pointer clicks/taps inside native viewport directly to interactive menus first
            menu_states = (STATE_TITLE, STATE_CHAR_SELECT, STATE_GAME_MODE, STATE_MP_LOBBY)
            ptr_pos = self._get_pointer_pos(event)
            handled_by_menu = False
            if ptr_pos and self.state in menu_states:
                wx, wy = ptr_pos
                vx, vy = self.view_offset
                vw, vh = int(GAME_W * self.view_scale), int(GAME_H * self.view_scale)
                if vx <= wx < vx + vw and vy <= wy < vy + vh:
                    nx, ny = self.window_to_native(wx, wy)
                    if self.state == STATE_TITLE:
                        handled_by_menu = self.title_screen.handle_pointer_down(nx, ny, audio_mgr=self.audio)
                    elif self.state == STATE_CHAR_SELECT:
                        handled_by_menu = self.char_select.handle_pointer_down(nx, ny, audio_mgr=self.audio)
                    elif self.state == STATE_GAME_MODE:
                        handled_by_menu = self.game_mode_screen.handle_pointer_down(nx, ny, audio_mgr=self.audio)
                    elif self.state == STATE_MP_LOBBY:
                        handled_by_menu = self.mp_lobby_screen.handle_pointer_down(nx, ny, audio_mgr=self.audio)
                    # On desktop mouse clicks inside menus, consume click so virtual touch buttons don't pop up
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        continue
                    if handled_by_menu:
                        continue

            # Touch Controller
            self.touch_ctrl.handle_event(event)

            if self.state == STATE_TITLE:
                self.title_screen.handle_event(event)
            elif self.state == STATE_CHAR_SELECT:
                self.char_select.handle_event(event, audio_mgr=self.audio)
            elif self.state == STATE_GAME_MODE:
                self.game_mode_screen.handle_event(event, audio_mgr=self.audio)
            elif self.state == STATE_MP_LOBBY:
                self.mp_lobby_screen.handle_event(event, audio_mgr=self.audio)
            elif self.state == STATE_PLAY:
                if event.type == pygame.KEYDOWN:
                    if event.key in KEYS_PAUSE:
                        self.pause_menu.reset()
                        self.state = STATE_PAUSE
                        self.player.moving = False
                        self.audio.play_sfx("pause", "ui")
                    elif event.key in KEYS_INVENTORY:
                        self.inv_screen.open(self.inventory, on_use_item=self._use_inventory_item)
                        self.state = STATE_INVENTORY
                        self.audio.play_sfx("pause", "ui")
                    elif event.key in KEYS_INTERACT:
                        if self.interact_cooldown <= 0:
                            self._interact()
            elif self.state == STATE_PAUSE:
                self.pause_menu.handle_event(event, audio_mgr=self.audio, touch_ctrl=self.touch_ctrl)
            elif self.state == STATE_DIALOGUE:
                self.dialogue.handle_event(event, audio_mgr=self.audio)
            elif self.state == STATE_INVENTORY:
                self.inv_screen.handle_event(event, audio_mgr=self.audio)
            elif self.state == STATE_QUESTS:
                self.quest_screen.handle_event(event)

        # Touch Controller One-shot triggers
        if self.state == STATE_PLAY:
            if self.touch_ctrl.consume_start() or self.touch_ctrl.consume_menu():
                self.pause_menu.reset()
                self.state = STATE_PAUSE
                self.player.moving = False
                self.audio.play_sfx("pause", "ui")
            elif self.touch_ctrl.consume_select() or self.touch_ctrl.consume_inv():
                self.inv_screen.open(self.inventory, on_use_item=self._use_inventory_item)
                self.state = STATE_INVENTORY
                self.audio.play_sfx("pause", "ui")
            elif self.touch_ctrl.consume_a():
                if self.interact_cooldown <= 0:
                    self._interact()

        elif self.state == STATE_DIALOGUE:
            if self.touch_ctrl.consume_a() or self.touch_ctrl.consume_b() or self.touch_ctrl.consume_start():
                self.dialogue.handle_event(None, touch_confirm=True, audio_mgr=self.audio)

        elif self.state == STATE_PAUSE:
            if self.touch_ctrl.consume_start() or self.touch_ctrl.consume_b():
                self.state = STATE_PLAY
                self.audio.play_sfx("menu_cancel", "ui")
            elif self.touch_ctrl.consume_up():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
                self.pause_menu.handle_event(dummy, audio_mgr=self.audio, touch_ctrl=self.touch_ctrl)
            elif self.touch_ctrl.consume_down():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
                self.pause_menu.handle_event(dummy, audio_mgr=self.audio, touch_ctrl=self.touch_ctrl)
            elif self.touch_ctrl.consume_left():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)
                self.pause_menu.handle_event(dummy, audio_mgr=self.audio, touch_ctrl=self.touch_ctrl)
            elif self.touch_ctrl.consume_right():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
                self.pause_menu.handle_event(dummy, audio_mgr=self.audio, touch_ctrl=self.touch_ctrl)
            elif self.touch_ctrl.consume_a():
                dummy_enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                self.pause_menu.handle_event(dummy_enter, audio_mgr=self.audio, touch_ctrl=self.touch_ctrl)

        elif self.state == STATE_INVENTORY:
            if self.touch_ctrl.consume_select() or self.touch_ctrl.consume_b() or self.touch_ctrl.consume_start():
                self.state = STATE_PLAY
                self.audio.play_sfx("menu_cancel", "ui")
            elif self.touch_ctrl.consume_up():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
                self.inv_screen.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_down():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
                self.inv_screen.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_left():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)
                self.inv_screen.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_right():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
                self.inv_screen.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_a():
                dummy_enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                self.inv_screen.handle_event(dummy_enter, audio_mgr=self.audio)

        elif self.state == STATE_TITLE:
            if self.touch_ctrl.consume_up():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
                self.title_screen.handle_event(dummy)
            elif self.touch_ctrl.consume_down():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
                self.title_screen.handle_event(dummy)
            elif self.touch_ctrl.consume_a() or self.touch_ctrl.consume_start():
                dummy_space = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
                self.title_screen.handle_event(dummy_space)

        elif self.state == STATE_CHAR_SELECT:
            if self.touch_ctrl.consume_left():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)
                self.char_select.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_right():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
                self.char_select.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_up():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
                self.char_select.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_down():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
                self.char_select.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_a() or self.touch_ctrl.consume_start():
                dummy_enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                self.char_select.handle_event(dummy_enter, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_b() or self.touch_ctrl.consume_select():
                dummy_esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
                self.char_select.handle_event(dummy_esc, audio_mgr=self.audio)

        elif self.state == STATE_GAME_MODE:
            if self.touch_ctrl.consume_up():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
                self.game_mode_screen.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_down():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
                self.game_mode_screen.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_a() or self.touch_ctrl.consume_start():
                dummy_enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                self.game_mode_screen.handle_event(dummy_enter, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_b() or self.touch_ctrl.consume_select():
                dummy_esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
                self.game_mode_screen.handle_event(dummy_esc, audio_mgr=self.audio)

        elif self.state == STATE_MP_LOBBY:
            if self.touch_ctrl.consume_up():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
                self.mp_lobby_screen.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_down():
                dummy = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
                self.mp_lobby_screen.handle_event(dummy, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_a() or self.touch_ctrl.consume_start():
                dummy_enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                self.mp_lobby_screen.handle_event(dummy_enter, audio_mgr=self.audio)
            elif self.touch_ctrl.consume_b() or self.touch_ctrl.consume_select():
                dummy_esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
                self.mp_lobby_screen.handle_event(dummy_esc, audio_mgr=self.audio)

    def _update(self, dt_ms):
        self.touch_ctrl.update(dt_ms)
        self.notification.update(dt_ms)
        update_tile_animators(dt_ms)

        if self.interact_cooldown > 0:
            self.interact_cooldown -= dt_ms

        if self.state == STATE_TITLE:
            self.title_screen.update(dt_ms)
            if self.title_screen.done:
                choice = self.title_screen.choice
                if choice == "CONTINUE":
                    if self._load_game():
                        self.state = STATE_PLAY
                        self.audio.play_sfx("menu_select", "ui")
                    else:
                        self.title_screen.done = False
                elif choice == "NEW GAME":
                    self.char_select_origin = "new_game"
                    self.char_select.reset(self.player.character_id)
                    self.state = STATE_CHAR_SELECT
                    self.title_screen.done = False
                    self.audio.play_sfx("menu_select", "ui")
                elif choice == "SELECT HERO":
                    self.char_select_origin = "title"
                    self.char_select.reset(self.player.character_id)
                    self.state = STATE_CHAR_SELECT
                    self.title_screen.done = False
                    self.audio.play_sfx("menu_select", "ui")
                elif choice == "QUIT":
                    self._stop_multiplayer()
                    self.running = False

        elif self.state == STATE_CHAR_SELECT:
            self.char_select.update(dt_ms)
            if self.char_select.done:
                if not self.char_select.canceled:
                    chosen_id = self.char_select.get_selected_id()
                    self.save_sys.save_selected_character(chosen_id)
                    self.player.set_character(chosen_id)
                    if self.char_select_origin == "new_game":
                        self.game_mode_screen.reset(chosen_id)
                        self.state = STATE_GAME_MODE
                        self.audio.play_sfx("menu_select", "ui")
                    else:
                        self.state = STATE_TITLE
                        self.title_screen.done = False
                        self.audio.play_sfx("menu_select", "ui")
                else:
                    self.state = STATE_TITLE
                    self.title_screen.done = False
                    self.audio.play_sfx("menu_cancel", "ui")

        elif self.state == STATE_GAME_MODE:
            self.game_mode_screen.update(dt_ms)
            if self.game_mode_screen.done:
                choice = self.game_mode_screen.choice
                if choice == "SOLO":
                    self.is_multiplayer = False
                    self._new_game(character_id=self.player.character_id)
                    self.state = STATE_PLAY
                    self.audio.play_sfx("menu_select", "ui")
                elif choice == "PLAY WITH FRIENDS":
                    self.mp_lobby_screen.reset(character_id=self.player.character_id)
                    self.state = STATE_MP_LOBBY
                    self.audio.play_sfx("menu_select", "ui")
                elif choice == "BACK":
                    self.char_select.reset(self.player.character_id)
                    self.state = STATE_CHAR_SELECT
                    self.audio.play_sfx("menu_cancel", "ui")

        elif self.state == STATE_MP_LOBBY:
            self.mp_lobby_screen.update(dt_ms)
            if self.mp_lobby_screen.session_ready and self.mp_lobby_screen.done:
                self._start_multiplayer_session()
            elif self.mp_lobby_screen.canceled and self.mp_lobby_screen.done:
                self.game_mode_screen.reset(self.player.character_id)
                self.state = STATE_GAME_MODE
                self.audio.play_sfx("menu_cancel", "ui")

        elif self.state == STATE_PLAY:
            self.play_time += dt_ms / 1000.0
            self.player.update(dt_ms, self.current_map.collision, touch_ctrl=self.touch_ctrl, audio_mgr=self.audio)
            self.camera.update(self.player.center_x, self.player.center_y)

            # Multiplayer Synchronization
            if self.is_multiplayer and self.network_worker:
                rem_updates = self.network_worker.get_remote_updates()
                if rem_updates and self.remote_player:
                    self.remote_player.apply_network_state(rem_updates[-1])

                if self.remote_player:
                    self.remote_player.update(dt_ms)

                for ev_type, ev_data in self.network_worker.get_events():
                    if ev_type in (NetworkWorker.EVENT_PLAYER_LEFT, NetworkWorker.EVENT_DISCONNECTED):
                        self.notification.show("Partner disconnected!")

                self.network_worker.queue_local_update({
                    "character_id": self.player.character_id,
                    "x": self.player.x,
                    "y": self.player.y,
                    "direction": self.player.direction,
                    "moving": self.player.moving,
                    "map": self.current_map_id
                })

            # NPCs idle animation
            for npc_id, anim in self.npc_animators.items():
                anim.update(dt_ms, False, None)

            # Enemies update & combat collision
            if hasattr(self.current_map, "enemies"):
                for enemy in self.current_map.enemies:
                    enemy.update(dt_ms, self.player, self.current_map.collision)
                    if enemy.is_alive and self.player.col_rect.colliderect(enemy.col_rect):
                        ex = enemy.x + enemy.fw // 2
                        ey = enemy.y + enemy.fh // 2
                        px, py = self.player.center_x, self.player.center_y
                        dist = max(1.0, math.hypot(px - ex, py - ey))
                        k_dir = ((px - ex) / dist, (py - ey) / dist)

                        hurt = self.player.take_damage(enemy.atk, k_dir)
                        if hurt:
                            self.audio.play_sfx("hurt.wav", "player")
                            if self.player.hp <= 0:
                                self._handle_player_faint()

            # Warps check
            for warp in self.current_map.warps:
                if self.player.col_rect.colliderect(warp.rect):
                    self._do_warp(warp)
                    break

        elif self.state == STATE_TRANSITION:
            self.transition.update(dt_ms)
            if not self.transition.active:
                self.state = STATE_PLAY

        elif self.state == STATE_PAUSE:
            if self.pause_menu.done:
                choice = self.pause_menu.choice
                if choice == "RESUME":
                    self.state = STATE_PLAY
                elif choice == "INVENTORY":
                    self.inv_screen.open(self.inventory, on_use_item=self._use_inventory_item)
                    self.state = STATE_INVENTORY
                elif choice == "QUESTS":
                    self.quest_screen.open(self.quest_mgr)
                    self.state = STATE_QUESTS
                elif choice == "SAVE":
                    self._save_game()
                    self.state = STATE_PLAY
                elif choice == "QUIT":
                    self._stop_multiplayer()
                    self.running = False
                self.pause_menu.done = False

        elif self.state == STATE_DIALOGUE:
            self.dialogue.update(dt_ms, audio_mgr=self.audio)
            if not self.dialogue.is_active():
                self.state = STATE_PLAY

        elif self.state == STATE_INVENTORY:
            if self.inv_screen.done:
                self.pause_menu.reset()
                self.state = STATE_PAUSE

        elif self.state == STATE_QUESTS:
            if self.quest_screen.done:
                self.pause_menu.reset()
                self.state = STATE_PAUSE

    def _draw(self):
        self.native.fill(COLOR_LIGHTEST)

        if self.state == STATE_TITLE:
            self.title_screen.draw(self.native)

        elif self.state == STATE_CHAR_SELECT:
            self.char_select.draw(self.native)

        elif self.state == STATE_GAME_MODE:
            self.game_mode_screen.draw(self.native)

        elif self.state == STATE_MP_LOBBY:
            self.mp_lobby_screen.draw(self.native)

        elif self.state in (STATE_PLAY, STATE_PAUSE, STATE_DIALOGUE, STATE_TRANSITION):
            # Draw world layers
            self.current_map.draw_ground(self.native, self.camera)
            if hasattr(self.current_map, "draw_ground_structures"):
                self.current_map.draw_ground_structures(self.native, self.camera)
            self.current_map.draw_props(self.native, self.camera)
            self.current_map.draw_items(self.native, self.camera, self.flags)

            # Draw NPCs, Player, and Y-sorted Structures (trees, buildings, towers)
            render_items = []
            if hasattr(self.current_map, "structures"):
                for st in self.current_map.structures:
                    if not getattr(st, "is_ground", False):
                        render_items.append((st.base_y, "structure", st, None))

            for npc in self.current_map.npcs:
                anim = self.npc_animators.get(npc.npc_id)
                if anim:
                    render_items.append((npc.y, "npc", npc, anim))

            if hasattr(self.current_map, "enemies"):
                for enemy in self.current_map.enemies:
                    if enemy.is_alive or enemy.death_timer > 0:
                        render_items.append((enemy.y + enemy.fh, "enemy", enemy, None))

            render_items.append((self.player.y, "player", self.player, None))

            if self.is_multiplayer and self.remote_player and self.remote_player.current_map == self.current_map_id:
                render_items.append((self.remote_player.y, "remote_player", self.remote_player, None))

            render_items.sort(key=lambda it: it[0])

            for y_pos, kind, entity, anim in render_items:
                if kind == "structure":
                    surf = entity.get_surface()
                    sx, sy = self.camera.apply(entity.px, entity.py)
                    self.native.blit(surf, (sx, sy))
                elif kind == "npc":
                    frame = anim.get_frame()
                    fw, fh = frame.get_size()
                    draw_x = entity.x - (fw - 16) // 2
                    draw_y = entity.y - (fh - 16)
                    sx, sy = self.camera.apply(draw_x, draw_y)
                    self.native.blit(frame, (sx, sy))
                elif kind == "enemy":
                    entity.draw(self.native, self.camera)
                elif kind == "remote_player":
                    entity.draw(self.native, self.camera)
                else:
                    self.player.draw(self.native, self.camera)

            # Interaction Prompt Pill when near a target
            if self.state == STATE_PLAY:
                nearby = self._get_nearby_target()
                if nearby:
                    prompt_text = "[SPACE] Talk" if nearby[0] == "npc" else "[SPACE] Check"
                    f = font_tag()
                    pw = f.size(prompt_text)[0] + 8
                    px = (GAME_W - pw) // 2
                    self.ui.draw_box(self.native, px, 3, pw, 13, fill=COLOR_LIGHT, border=COLOR_DARKEST)
                    self.ui.draw_text_centered(self.native, prompt_text, 5, COLOR_DARKEST, f)

            # Draw Dialogue Box on top
            if self.state == STATE_DIALOGUE:
                self.dialogue.draw(self.native)

            # Draw Pause Menu on top
            if self.state == STATE_PAUSE:
                self.pause_menu.draw(self.native, self.player, audio_mgr=self.audio, touch_ctrl=self.touch_ctrl)

            # Transitions
            if self.state == STATE_TRANSITION:
                self.transition.draw(self.native)

        elif self.state == STATE_INVENTORY:
            self.inv_screen.draw(self.native, self.player)

        elif self.state == STATE_QUESTS:
            self.quest_screen.draw(self.native)

        # In-game notification bar
        self.notification.draw(self.native)

        # Scale to window with preserved pixel-art aspect ratio (Letterbox / Pillarbox)
        scr_w, scr_h = self.screen.get_size()
        scale = min(scr_w / GAME_W, scr_h / GAME_H)
        view_w = int(GAME_W * scale)
        view_h = int(GAME_H * scale)
        view_x = (scr_w - view_w) // 2
        view_y = 0 if scr_h > (scr_w * 1.1) else (scr_h - view_h) // 2
        self.view_scale = scale
        self.view_offset = (view_x, view_y)

        self.screen.fill((9, 27, 29))  # Dark retro letterbox border
        scaled = pygame.transform.scale(self.native, (view_w, view_h))
        self.screen.blit(scaled, (view_x, view_y))

        # Render touch overlay on top of screen
        self.touch_ctrl.draw(self.screen)

        pygame.display.flip()


async def async_main():
    game = Game()
    await game.run()


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
