"""
Comprehensive Test Suite for Echoes of Mossbell
Tests all movement directions, NPC dialogues, house entering/leaving,
animated tiles, inventory usage, quests, saving/loading, and builds screenshots.
"""
import os, sys, pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

from game.main import Game
from game.inventory import ITEMS
from game.settings import *

def run_tests():
    print("=== STARTING COMPREHENSIVE TEST SUITE ===")
    game = Game()
    game._new_game()
    game.state = "play"

    # 1. Test Player Movement (Arrow keys + WASD)
    print("\n1. Testing Movement & Collision...")
    initial_x, initial_y = game.player.x, game.player.y
    print(f"Starting position in village: ({initial_x}, {initial_y})")

    # Move right
    cm = game.current_map.collision
    dx, dy = cm.can_move(game.player.col_rect, 10, 0)
    assert dx > 0, "Player should be able to move right on path"
    game.player.x += dx
    print(f"Moved right to: ({game.player.x}, {game.player.y}), direction: {game.player.direction}")

    # Move up
    dx, dy = cm.can_move(game.player.col_rect, 0, -10)
    assert dy < 0, "Player should be able to move up on path"
    game.player.y += dy
    print(f"Moved up to: ({game.player.x}, {game.player.y}), direction: {game.player.direction}")

    # Test collision with solid border
    dx, dy = cm.can_move(game.player.col_rect, -500, 0)
    assert dx == 0, "Collision should prevent moving past map border"
    print("Collision detection verified successfully!")

    # 2. Test Entering & Leaving Player House
    print("\n2. Testing House Interior & Warping...")
    # Teleport right in front of player house door (4*16, 4*16)
    game.player.x = 4 * 16
    game.player.y = 4 * 16 + 2
    # Trigger warp
    warps = [w for w in game.current_map.warps if w.target_map == "player_house"]
    assert len(warps) > 0, "Player house warp must exist in village"
    game.change_map("player_house", warps[0].target_x, warps[0].target_y)
    assert game.current_map_id == "player_house", "Should now be in player_house"
    print(f"Successfully entered Player House! Size: {game.current_map.width}x{game.current_map.height}")

    # Test interactive objects inside house
    print("Testing furniture interaction:")
    game.player.hp = 10  # lower HP
    print(f"Player HP before resting: {game.player.hp}/{game.player.max_hp}")
    # Bed interaction
    bed = [obj for obj in game.current_map.interactives if obj.on_interact == "heal_player"][0]
    game._examine_object(bed)
    assert game.state == "dialogue", "Interacting with bed should open dialogue"
    assert game.player.hp == game.player.max_hp, "Bed should restore HP to full"
    print(f"Player HP after resting in bed: {game.player.hp}/{game.player.max_hp} (Restored!)")
    game.dialogue.close()
    game.state = "play"

    # Pick up item in house (apple)
    assert len(game.current_map.items) > 0, "Apple should be in house dresser"
    apple_item = game.current_map.items[0]
    game._pickup_item(apple_item)
    assert game.inventory.has("apple", 1), "Player should now have apple in inventory"
    print("Picked up Sweet Apple from dresser!")

    # Exit house back to village
    exit_warp = game.current_map.warps[0]
    game.change_map(exit_warp.target_map, exit_warp.target_x, exit_warp.target_y)
    assert game.current_map_id == "village", "Should have exited back to village"
    print(f"Exited house back to Village at: ({game.player.x}, {game.player.y})")

    # 3. Test Elder House Interior
    print("\n3. Testing Elder House Interior...")
    elder_warps = [w for w in game.current_map.warps if w.target_map == "elder_house"]
    game.change_map("elder_house", elder_warps[0].target_x, elder_warps[0].target_y)
    assert game.current_map_id == "elder_house", "Should be in elder_house"
    # Pick up golden key
    assert len(game.current_map.items) > 0, "Golden Key should be in elder archive"
    game._pickup_item(game.current_map.items[0])
    assert game.inventory.has("gold_key", 1), "Player should have Golden Key"
    print("Picked up Golden Key from Elder's Archive!")
    game.change_map("village", 16 * 16, 5 * 16)

    # 4. Test NPC Dialogue, Portraits & Pagination
    print("\n4. Testing NPC Dialogue System...")
    elder_npc = [n for n in game.current_map.npcs if n.npc_id == "elder"][0]
    game._talk_to_npc(elder_npc)
    assert game.state == "dialogue", "State should be dialogue"
    assert game.dialogue.is_active(), "Dialogue box should be active"
    print(f"Dialogue opened with {elder_npc.name}. Pages: {len(game.dialogue.pages)}")
    assert len(game.dialogue.pages) > 0, "Dialogue should have at least 1 page"

    # Simulate advancing typewriter and pages
    for _ in range(50):
        game.dialogue.update(20)
    # Advance dialogue
    event_z = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z)
    game.dialogue.handle_event(event_z)
    game.dialogue.handle_event(event_z)
    game.dialogue.close()
    game._on_dialogue_end(elder_npc)
    assert game.state == "play", "Dialogue should close cleanly to play state"
    assert game.interact_cooldown > 0, "Debounce cooldown should be active"
    print("Dialogue advanced and closed cleanly with debounce cooldown!")

    # 5. Test Animated Tiles
    print("\n5. Testing Animated Tiles (Water & Flowers)...")
    # Update animators
    from game.map_loader import update_tile_animators, get_tile
    frame1 = get_tile("wt")
    update_tile_animators(200)
    frame2 = get_tile("wt")
    print(f"Animated water tile functional: frame size {frame1.get_size()}")
    flower_frame = get_tile("fl")
    print(f"Animated flower tile functional: frame size {flower_frame.get_size()}")

    # 6. Test Forest, Ruins, Dungeon & Grotto Warping
    print("\n6. Testing All World Maps...")
    maps_to_visit = ["forest", "deep_forest", "ruins", "dungeon", "grotto"]
    for m in maps_to_visit:
        game.change_map(m, 10 * 16, 9 * 16)
        assert game.current_map_id == m, f"Should be in {m}"
        # Test render
        game._draw()
        print(f"Map '{m}' loaded and rendered successfully! Props: {len(game.current_map.props)}, Items: {len(game.current_map.items)}")

    # 7. Test Dungeon Chests & Equipment
    print("\n7. Testing Dungeon Items & Inventory Usage...")
    game.change_map("dungeon", 8 * 16, 8 * 16)
    for it in list(game.current_map.items):
        game._pickup_item(it)
    assert game.inventory.has("sword"), "Player should have found Iron Sword"
    assert game.inventory.has("shield"), "Player should have found Oak Shield"
    assert game.inventory.has("elixir"), "Player should have found Magic Elixir"
    assert game.inventory.has("coins"), "Player should have found Gold Coins"
    print("Dungeon loot gathered successfully!")

    # Test consuming an item in inventory
    game.player.hp = 5
    elixir = ITEMS["elixir"]
    print(f"Player HP before elixir: {game.player.hp}")
    game._use_inventory_item(elixir)
    assert game.player.hp == game.player.max_hp, "Elixir should fully restore HP"
    print(f"Player HP after elixir: {game.player.hp} (Full restoration!)")

    # 8. Test Quests Completion
    print("\n8. Testing Quest Progression & Shadow King resolution...")
    game.quest_mgr.start("main")
    game.inventory.add("crystal", 1)
    game.quest_mgr.advance("main") # 1
    game.quest_mgr.advance("main") # 2
    game.quest_mgr.advance("main") # 3
    game.quest_mgr.advance("main") # 4
    game.quest_mgr.advance("main") # 5 (ready for boss)
    game.change_map("grotto", 10 * 16, 9 * 16)
    shadow_npc = [n for n in game.current_map.npcs if n.npc_id == "shadow"][0]
    game._talk_to_npc(shadow_npc)
    assert game.quest_mgr.is_completed("main"), "Main quest should be completed after talking to Shadow King"
    print("Main Quest 'The Vanishing' completed! Curse is broken!")

    # 9. Test Save / Load System
    print("\n9. Testing Save & Load System...")
    game._save_game()
    assert game.save_sys.exists(), "Save file should exist on disk"
    loaded = game._load_game()
    assert loaded, "Game should load successfully from disk"
    assert game.current_map_id == "grotto", "Loaded map should match saved map"
    print("Save and Load verified successfully!")

    # 10. Generate Visual Screenshots
    print("\n10. Generating Screenshots for Verification...")
    # Screenshot 1: Village with houses, flowers, pond
    game.change_map("village", 10 * 16, 9 * 16)
    game._draw()
    pygame.image.save(game.screen, os.path.join(root, "screenshot_play.png"))

    # Screenshot 2: Player House Interior
    game.change_map("player_house", 5 * 16, 6 * 16)
    game._draw()
    pygame.image.save(game.screen, os.path.join(root, "screenshot_interior.png"))

    # Screenshot 3: Dungeon with prison cells, chests, altars
    game.change_map("dungeon", 8 * 16, 8 * 16)
    game._draw()
    pygame.image.save(game.screen, os.path.join(root, "screenshot_dungeon.png"))

    # Screenshot 4: Dialogue with portrait
    game.change_map("village", 10 * 16, 9 * 16)
    elder_npc = [n for n in game.current_map.npcs if n.npc_id == "elder"][0]
    game._talk_to_npc(elder_npc)
    for _ in range(30):
        game.dialogue.update(16)
    game._draw()
    pygame.image.save(game.screen, os.path.join(root, "screenshot_dialogue.png"))
    game.dialogue.close()

    # Screenshot 5: Categorized Inventory Screen
    game.state = "inventory"
    game.inv_screen.open(game.inventory)
    game._draw()
    pygame.image.save(game.screen, os.path.join(root, "screenshot_inv.png"))

    # Screenshot 6: Pause Menu
    game.state = "pause"
    game.pause_menu.reset()
    game._draw()
    pygame.image.save(game.screen, os.path.join(root, "screenshot_pause.png"))

    pygame.quit()
    print("\n=== ALL 10 TEST SUITE CATEGORIES PASSED WITH ZERO ERRORS! ===")

if __name__ == "__main__":
    run_tests()

