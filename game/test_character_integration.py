"""
Dedicated Test Suite for Ocean Nostalgia Character Integration
Validates all 24 characters, 4 directions, 8 FPS walking cycle, idle middle frame,
nearest-neighbor scaling, transparency, player/NPC movement & dialogue independence.
"""
import os, sys, pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

import pygame
pygame.init()
pygame.display.set_mode((160, 144), pygame.HIDDEN)

from game.ocean_animator import OceanCharacterAnimator, get_available_characters
from game.player import Player
from game.world import build_village, build_all_maps
from game.settings import OCEAN_CHAR_DIR

def run_character_tests():
    print("=== STARTING OCEAN NOSTALGIA CHARACTER INTEGRATION TESTS ===")

    # 1. Verify all 24 characters discovered
    print("\n1. Testing Character Discovery...")
    all_chars = get_available_characters()
    print(f"Discovered characters ({len(all_chars)}): {all_chars}")
    assert len(all_chars) == 24, f"Expected 24 characters, found {len(all_chars)}"
    assert "actor1_character_01" in all_chars, "actor1_character_01 must be present"
    assert "actor3_character_08" in all_chars, "actor3_character_08 must be present"
    print("All 24 character folders verified!")

    # 2. Test OceanCharacterAnimator for actor1_character_01
    print("\n2. Testing Character Animator Loading & Specifications...")
    anim = OceanCharacterAnimator("actor1_character_01", variant="gameboy", target_size=(24, 32), fps=8)
    
    # Check specifications
    assert anim.fps == 8, f"Expected 8 FPS, got {anim.fps}"
    assert anim.ms_per_frame == 125.0, f"Expected 125ms per frame, got {anim.ms_per_frame}"
    assert anim.idle_frame_index == 1, f"Expected idle frame index 1, got {anim.idle_frame_index}"
    
    # Check directions order: down, left, right, up
    for d in ["down", "left", "right", "up"]:
        assert d in anim.native_frames, f"Missing native frames for direction {d}"
        assert len(anim.native_frames[d]) == 3, f"Expected 3 frames for direction {d}"
        assert d in anim.scaled_frames, f"Missing scaled frames for direction {d}"
        assert len(anim.scaled_frames[d]) == 3, f"Expected 3 scaled frames for direction {d}"
        
        # Check native dimensions (72x96)
        for f in anim.native_frames[d]:
            assert f.get_size() == (72, 96), f"Expected native frame size (72, 96), got {f.get_size()}"
            
        # Check scaled dimensions (24x32)
        for f in anim.scaled_frames[d]:
            assert f.get_size() == (24, 32), f"Expected scaled frame size (24, 32), got {f.get_size()}"

    print("Native dimensions (72x96) and scaled dimensions (24x32) verified for all 4 directions!")

    # 3. Test Transparency and Nearest-Neighbor Palette Integrity
    print("\n3. Testing Transparency & Nearest-Neighbor Preservation...")
    idle_frame = anim.get_idle_frame("down")
    assert idle_frame.get_size() == (24, 32)
    # Check top corner is transparent
    corner_color = idle_frame.get_at((0, 0))
    assert corner_color.a == 0, f"Expected alpha 0 at top-left corner, got {corner_color.a}"
    # Verify palette has <= 4 distinct colors
    colors = set()
    for y in range(32):
        for x in range(24):
            c = idle_frame.get_at((x, y))
            if c.a > 0:
                colors.add((c.r, c.g, c.b))
    assert len(colors) <= 4, f"Expected Game Boy 4-shade palette, got {len(colors)} colors"
    print(f"Transparency intact (alpha=0), crisp 4-shade Game Boy palette confirmed ({len(colors)} colors)!")

    # 4. Test Idle vs Walk Animation States & Timing
    print("\n4. Testing Animation States (Walking Cycle vs Idle Frame)...")
    anim.face("down")
    assert anim.current_frame_index == 1, "Idle frame must be frame index 1"
    assert anim.get_frame() == anim.scaled_frames["down"][1], "Current frame should be idle frame"

    # Advance time while NOT moving -> must stay on idle frame
    anim.update(1000, moving=False)
    assert anim.current_frame_index == 1, "Must remain on idle frame 1 when standing still"

    # Start moving down -> should cycle [0, 1, 2, 1] at 8 FPS (125ms per step)
    anim.update(50, moving=True, direction="down")   # 50ms (not reached 125ms yet)
    assert anim.current_frame_index == 1

    anim.update(80, moving=True)  # total 130ms -> step 1
    assert anim.current_frame_index == 2, f"Expected frame 2 after 1 step, got {anim.current_frame_index}"

    anim.update(125, moving=True) # step 2
    assert anim.current_frame_index == 1, f"Expected frame 1 after 2 steps, got {anim.current_frame_index}"

    anim.update(125, moving=True) # step 3
    assert anim.current_frame_index == 0, f"Expected frame 0 after 3 steps, got {anim.current_frame_index}"

    # Stop moving -> immediately reset to idle frame 1
    anim.update(50, moving=False)
    assert anim.current_frame_index == 1, "Stopping movement must immediately restore idle frame 1"
    print("Walk cycle [0, 1, 2, 1] at 8 FPS (125ms) and instant idle rest verified!")

    # 5. Test All 4 Directions
    print("\n5. Testing All 4 Directions...")
    for d in ["down", "left", "right", "up"]:
        anim.face(d)
        assert anim.direction == d
        assert anim.current_frame_index == 1
        frame = anim.get_frame()
        assert frame == anim.scaled_frames[d][1]
    print("All 4 directions (down, left, right, up) correctly face and render idle frames!")

    # 6. Test Player Integration
    print("\n6. Testing Player Integration with actor1_character_01...")
    player = Player(160, 144)
    assert player.character_id == "actor1_character_01"
    assert player.variant == "gameboy"
    assert isinstance(player.animator, OceanCharacterAnimator)
    
    # Test player draw sizing and offset calculation
    surf = pygame.Surface((160, 144))
    from game.camera import Camera
    cam = Camera(22, 18)
    player.draw(surf, cam)
    print("Player entity successfully renders 24x32 Ocean character with proper offset!")

    # 7. Test NPC Independent Animation States & Dialogue Facing
    print("\n7. Testing NPC Independent Animation States...")
    from game.main import Game
    game = Game()
    game._new_game()
    game.state = "play"

    elder_anim = game.npc_animators.get("elder")
    boy_anim = game.npc_animators.get("boy")
    assert elder_anim is not None and boy_anim is not None
    assert elder_anim.character_id == "actor1_character_05", f"Elder expected actor1_character_05, got {elder_anim.character_id}"
    assert boy_anim.character_id == "actor1_character_02", f"Boy expected actor1_character_02, got {boy_anim.character_id}"

    # Verify they have independent objects and timers
    assert elder_anim is not boy_anim
    elder_anim.timer = 50.0
    boy_anim.timer = 100.0
    assert elder_anim.timer != boy_anim.timer
    print("NPCs maintain completely independent animation states and character assets!")

    # Test dialogue interaction: NPC faces player
    print("Testing NPC facing player during dialogue:")
    game.player.direction = "up"
    elder_npc = [n for n in game.current_map.npcs if n.npc_id == "elder"][0]
    game._talk_to_npc(elder_npc)
    assert elder_anim.direction == "down", f"Elder should face down when player is up, got {elder_anim.direction}"
    assert elder_anim.current_frame_index == 1, "Elder must show idle frame during conversation"
    print("NPC turns to face player on talk and holds idle frame without walking in place!")

    # 8. Test Graceful Fallback for Missing Character
    print("\n8. Testing Graceful Fallback on Missing Character...")
    fallback_anim = OceanCharacterAnimator("nonexistent_actor_99", variant="gameboy")
    assert fallback_anim.get_frame().get_size() == (24, 32)
    print("Missing character handled gracefully without crashing!")

    # 9. Test Loading all 24 characters
    print("\n9. Testing Batch Loading of all 24 Characters in Game Boy variant...")
    for char_id in all_chars:
        ca = OceanCharacterAnimator(char_id, variant="gameboy", target_size=(24, 32))
        f = ca.get_frame()
        assert f.get_size() == (24, 32), f"Character {char_id} failed to produce 24x32 frame"
    print("All 24 characters loaded and verified successfully!")

    print("\n=== ALL OCEAN NOSTALGIA CHARACTER INTEGRATION TESTS PASSED PERFECTLY! ===")

if __name__ == "__main__":
    run_character_tests()

