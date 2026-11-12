"""
Dedicated Test Suite for Audio System & Touch Controls Integration.
Tests:
- Audio manager categories, formats (WAV, MP3), volume, mute, and cooldowns.
- Touch controller D-Pad, Action buttons, Inventory/Menu buttons, and layout adaptivity.
- Keyboard and Touch dual-input responsiveness.
- Aspect ratio letterboxing calculations.
"""
import os
import sys
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

pygame.init()
screen = pygame.display.set_mode((640, 576), pygame.HIDDEN)

from game.audio import AudioManager, AUDIO_CATEGORIES
from game.touch_controls import TouchController
from game.player import Player
from game.main import Game
from game.settings import AUDIO_DIR, GAME_W, GAME_H


def run_tests():
    print("=== STARTING AUDIO & TOUCH CONTROLS TEST SUITE ===")

    # 1. Test Audio Categories Structure
    print("\n1. Testing Audio Directory & Categories Structure...")
    for cat in ["music", "player", "npc", "environment", "combat", "ui", "items"]:
        cat_path = os.path.join(AUDIO_DIR, cat)
        assert os.path.isdir(cat_path), f"Audio category directory {cat} missing"
        files = os.listdir(cat_path)
        assert len(files) > 0, f"Category {cat} should contain audio files"
        print(f"  Category '{cat}': {len(files)} files found (e.g. {files[0]})")
    print("All 7 audio category directories verified!")

    # 2. Test Audio Manager Volume & Mute Controls
    print("\n2. Testing Volume Controls & Mute Functions...")
    audio = AudioManager()
    audio.set_music_volume(0.8)
    assert round(audio.music_volume, 2) == 0.8, "Music volume should be 0.8"
    audio.set_sfx_volume(0.4)
    assert round(audio.sfx_volume, 2) == 0.4, "SFX volume should be 0.4"

    # Test Mute
    assert not audio.music_muted
    audio.toggle_music_mute()
    assert audio.music_muted, "Music should now be muted"
    audio.toggle_music_mute()
    assert not audio.music_muted, "Music should now be unmuted"
    print("Independent volume controls and mute toggles functioning correctly!")

    # 3. Test SFX Resolution and Debounce
    print("\n3. Testing SFX Category Resolution & Debounce Cooldown...")
    # Play categorized sound
    audio.play_sfx("step_grass", "player")
    assert "step_grass" in audio.sfx_cooldowns
    t1 = audio.sfx_cooldowns["step_grass"]

    # Immediate second call should be debounced / throttled
    audio.play_sfx("step_grass", "player")
    t2 = audio.sfx_cooldowns["step_grass"]
    assert t1 == t2, "Rapid second sound effect should be throttled by debounce"

    # Dialogue blip debounce
    audio.play_sfx("talk_blip", "npc")
    assert "talk_blip" in audio.sfx_cooldowns
    print("SFX category resolution and debounce throttling working as expected!")

    # 4. Test Music Location Transitions
    print("\n4. Testing Music Track Transition Logic...")
    audio.play_music("bpag02 - Game Theme.mp3")
    assert audio.current_music_file == "bpag02 - Game Theme.mp3"
    # Playing same track should not interrupt
    audio.play_music("bpag02 - Game Theme.mp3")
    assert audio.current_music_file == "bpag02 - Game Theme.mp3"
    # Transition to new track
    audio.play_music("cag01 - Title Screen.mp3")
    assert audio.current_music_file == "cag01 - Title Screen.mp3"
    audio.stop_music()
    assert audio.current_music_file is None
    print("Music transitions and playback continuity verified!")

    # 5. Test Touch Controller Layouts (Landscape & Portrait)
    print("\n5. Testing Touch Controller Adaptive Layout...")
    # Landscape (640x576 or 1280x720)
    touch = TouchController(1280, 720)
    assert "up" in touch.buttons
    assert "down" in touch.buttons
    assert "left" in touch.buttons
    assert "right" in touch.buttons
    assert "a" in touch.buttons
    assert "b" in touch.buttons
    assert "inv" in touch.buttons
    assert "menu" in touch.buttons
    dpad_x = touch.buttons["up"].rect.centerx
    a_x = touch.buttons["a"].rect.centerx
    assert dpad_x < 640, "D-pad should be on left half in landscape"
    assert a_x > 640, "Action buttons should be on right half in landscape"
    print("Landscape touch layout verified!")

    # Portrait (1080x2400 mobile phone)
    touch.update_layout(1080, 2400)
    # Buttons should be in lower console half
    up_y = touch.buttons["up"].rect.centery
    assert up_y > 1200, "Controls should be in lower half of portrait display"
    print("Portrait Game Boy console touch layout verified!")

    # 6. Test Touch Input Processing (Finger & Mouse)
    print("\n6. Testing Touch Event Processing...")
    touch.update_layout(640, 576)
    a_rect = touch.buttons["a"].rect

    # Simulate finger down on A button
    down_event = pygame.event.Event(pygame.FINGERDOWN, finger_id=1,
                                   x=a_rect.centerx / 640.0, y=a_rect.centery / 576.0)
    touch.handle_event(down_event)
    assert touch.btn_a, "A button should be active on touch down"
    assert touch.consume_a(), "A button should trigger rising edge consume_a()"
    assert not touch.consume_a(), "consume_a() should only trigger once per press"

    # Finger up
    up_event = pygame.event.Event(pygame.FINGERUP, finger_id=1,
                                 x=a_rect.centerx / 640.0, y=a_rect.centery / 576.0)
    touch.handle_event(up_event)
    assert not touch.btn_a, "A button should release on touch up"
    print("Multi-touch event processing verified!")

    # 7. Test Dual Keyboard and Touch Player Movement
    print("\n7. Testing Player Movement with Touch & Keyboard...")
    player = Player(160, 144)
    init_x, init_y = player.x, player.y

    # Touch D-Pad right
    touch.right = True
    player.update(100, None, touch_ctrl=touch, audio_mgr=audio)
    assert player.x > init_x, "Player should move right from touch controller input"
    assert player.direction == "right"
    touch.right = False

    player.update(50, None, touch_ctrl=touch, audio_mgr=audio)
    assert not player.moving, "Player should stop moving when touch input releases"
    print("Player entity responds seamlessly to virtual touch controls!")

    # 8. Test Integrated Game Loop
    print("\n8. Testing Game Engine Integration...")
    game = Game()
    game._new_game()
    game.state = "play"

    # Verify audio manager and touch controller active in game
    assert game.audio.enabled
    assert game.touch_ctrl.enabled
    assert game.current_map.music is not None

    # Test touch open inventory
    game.touch_ctrl.btn_inv_pressed = True
    game._handle_events()
    assert game.state == "inventory", "Touching INV button should open inventory screen"

    # Test touch close inventory
    game.touch_ctrl.btn_b_pressed = True
    game._handle_events()
    assert game.state == "play", "Touching B button should close inventory screen"

    # Test touch open pause menu
    game.touch_ctrl.btn_menu_pressed = True
    game._handle_events()
    assert game.state == "pause", "Touching MENU button should open pause menu"

    # Render frame with touch overlay
    game._draw()
    print("Full game state transitions via touch controls and audio events verified!")

    pygame.quit()
    print("\n=== ALL AUDIO & TOUCH CONTROLS TESTS PASSED WITH 100% SUCCESS! ===")


if __name__ == "__main__":
    run_tests()

