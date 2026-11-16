"""
Centralized Audio Management System.
Features:
- Category-based audio asset resolution (music, player, npc, environment, combat, ui, items).
- Multi-format support (WAV, OGG, MP3).
- Debounce / cooldown system to prevent rapid SFX machine-gunning.
- Independent volume controls for Music and SFX.
- Full Mute / Unmute support.
- Smooth location music transitions (fadeout / prevent re-triggering same track).
- Completely local and offline with graceful degradation.
"""
import os
import time
import pygame
from game.settings import AUDIO_DIR, MUSIC_DIR, SFX_DIR

AUDIO_CATEGORIES = ["music", "player", "npc", "environment", "combat", "ui", "items"]


class AudioManager:
    """Centralized manager for all music and sound effects across the game."""

    def __init__(self):
        self.enabled = True
        self.sfx_cache = {}
        self.sfx_cooldowns = {}   # sound_key -> timestamp_ms

        # Volume state
        self.music_volume = 0.6
        self.sfx_volume = 0.7
        self.music_muted = False
        self.sfx_muted = False

        self.current_music_file = None

        # Debounce minimum intervals (in milliseconds)
        self.min_intervals = {
            "talk_blip": 55,
            "talk_low": 55,
            "talk_high": 55,
            "step_grass": 220,
            "step_stone": 220,
            "dash": 350,
            "menu_move": 60,
            "menu_select": 100,
            "item_pickup": 150,
            "hurt": 300,
            "hit_enemy": 150,
            "sword_swing": 200,
            "door_open": 500,
            "door_close": 500,
            "default": 60,
        }

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except Exception:
            self.enabled = False

    # ---- Music Management --------------------------------------------------
    def play_music(self, filename, loops=-1, fade_ms=400):
        """
        Plays background music for locations.
        Smoothly transitions between tracks and avoids restarting if already playing.
        """
        if not self.enabled or not filename:
            return

        # If already playing this track, don't restart
        if self.current_music_file == filename and pygame.mixer.music.get_busy():
            return

        path = self._resolve_music_path(filename)
        if not path or not os.path.isfile(path):
            return

        try:
            # Fade out existing music if playing a different track
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(fade_ms)
                pygame.time.delay(30)

            pygame.mixer.music.load(path)
            vol = 0.0 if self.music_muted else self.music_volume
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play(loops, fade_ms=fade_ms)
            self.current_music_file = filename
        except Exception:
            pass

    def stop_music(self, fade_ms=400):
        if not self.enabled:
            return
        try:
            pygame.mixer.music.fadeout(fade_ms)
            self.current_music_file = None
        except Exception:
            pass

    def pause_music(self):
        if not self.enabled:
            return
        try:
            pygame.mixer.music.pause()
        except Exception:
            pass

    def unpause_music(self):
        if not self.enabled:
            return
        try:
            pygame.mixer.music.unpause()
        except Exception:
            pass

    def set_music_volume(self, vol):
        """Sets music volume between 0.0 and 1.0."""
        self.music_volume = max(0.0, min(1.0, vol))
        if self.enabled and not self.music_muted:
            try:
                pygame.mixer.music.set_volume(self.music_volume)
            except Exception:
                pass

    def toggle_music_mute(self):
        """Toggles music mute state."""
        self.set_music_mute(not self.music_muted)
        return self.music_muted

    def set_music_mute(self, muted):
        self.music_muted = bool(muted)
        if self.enabled:
            try:
                vol = 0.0 if self.music_muted else self.music_volume
                pygame.mixer.music.set_volume(vol)
            except Exception:
                pass

    # ---- Sound Effects (SFX) ------------------------------------------------
    def play_sfx(self, sound_name, category=None):
        """
        Plays a sound effect with category resolution, format fallback, and debounce check.
        sound_name: e.g. "step_grass", "talk_blip.wav", "player/step_grass.wav", "SE - Bip.mp3"
        category: optional category hint ("player", "npc", "environment", "combat", "ui", "items")
        """
        if not self.enabled or self.sfx_muted or not sound_name:
            return

        # Debounce check
        base_key = os.path.splitext(os.path.basename(sound_name))[0]
        now_ms = time.time() * 1000.0
        min_interval = self.min_intervals.get(base_key, self.min_intervals["default"])
        last_played = self.sfx_cooldowns.get(base_key, 0.0)

        if (now_ms - last_played) < min_interval:
            return  # Throttle rapid repeated sound

        sound = self._get_sound(sound_name, category)
        if sound:
            try:
                sound.set_volume(self.sfx_volume)
                sound.play()
                self.sfx_cooldowns[base_key] = now_ms
            except Exception:
                pass

    def set_sfx_volume(self, vol):
        """Sets sound effects volume between 0.0 and 1.0."""
        self.sfx_volume = max(0.0, min(1.0, vol))
        if self.enabled:
            for s in self.sfx_cache.values():
                try:
                    s.set_volume(self.sfx_volume)
                except Exception:
                    pass

    def toggle_sfx_mute(self):
        """Toggles SFX mute state."""
        self.sfx_muted = not self.sfx_muted
        return self.sfx_muted

    def set_sfx_mute(self, muted):
        self.sfx_muted = bool(muted)

    # ---- Path & Cache Resolution -------------------------------------------
    def _resolve_music_path(self, filename):
        if os.path.isfile(filename):
            return filename
        p = os.path.join(MUSIC_DIR, filename)
        if os.path.isfile(p):
            return p
        p = os.path.join(AUDIO_DIR, filename)
        if os.path.isfile(p):
            return p
        return None

    def _get_sound(self, sound_name, category=None):
        if sound_name in self.sfx_cache:
            return self.sfx_cache[sound_name]

        path = self._resolve_sfx_path(sound_name, category)
        if not path:
            return None

        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(self.sfx_volume)
            self.sfx_cache[sound_name] = sound
            return sound
        except Exception:
            return None

    def _resolve_sfx_path(self, sound_name, category=None):
        """Searches across categories and formats (.wav, .ogg, .mp3)."""
        if os.path.isfile(sound_name):
            return sound_name

        candidates = []
        name_no_ext, ext = os.path.splitext(sound_name)
        extensions = [ext] if ext else [".wav", ".ogg", ".mp3"]

        if category:
            for e in extensions:
                candidates.append(os.path.join(AUDIO_DIR, category, f"{name_no_ext}{e}"))

        for cat in AUDIO_CATEGORIES:
            for e in extensions:
                candidates.append(os.path.join(AUDIO_DIR, cat, f"{name_no_ext}{e}"))

        for e in extensions:
            candidates.append(os.path.join(SFX_DIR, f"{name_no_ext}{e}"))
            candidates.append(os.path.join(AUDIO_DIR, f"{name_no_ext}{e}"))

        for c in candidates:
            if os.path.isfile(c):
                return c

        return None
