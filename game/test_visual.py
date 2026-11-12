"""Automated test: launch game, take screenshot, simulate input, then exit."""
import os
import sys
import time
import pygame

# Ensure project root on path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

from game.main import Game

def run_test():
    game = Game()
    
    # Run 30 frames on title screen
    for _ in range(30):
        game.clock.tick(60)
        # Pump events
        for event in pygame.event.get():
            pass
        game._update(16)
        game._draw()
    
    # Take screenshot of title
    pygame.image.save(game.screen, os.path.join(root, "screenshot_title.png"))
    print("Title screenshot saved")
    
    # Simulate pressing Z to start new game
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
    game.title_screen.handle_event(event)  # move to NEW GAME if CONTINUE is first
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z)
    game.title_screen.handle_event(event)
    game._update(16)
    
    # Check we entered play state
    print(f"State after start: {game.state}")
    
    # Run 120 frames in play
    for _ in range(120):
        game.clock.tick(60)
        for event in pygame.event.get():
            pass
        game._update(16)
        game._draw()
    
    # Take gameplay screenshot
    pygame.image.save(game.screen, os.path.join(root, "screenshot_play.png"))
    print("Play screenshot saved")
    
    # Test pause
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    game._handle_events_test = lambda: None
    game.state = "pause"
    game.pause_menu.reset()
    game._draw()
    pygame.image.save(game.screen, os.path.join(root, "screenshot_pause.png"))
    print("Pause screenshot saved")
    
    # Test inventory
    game.inventory.add("herb", 2)
    game.inventory.add("old_key")
    game.inv_screen.open(game.inventory)
    game.state = "inventory"
    game._draw()
    pygame.image.save(game.screen, os.path.join(root, "screenshot_inv.png"))
    print("Inventory screenshot saved")
    
    # Clean up
    pygame.quit()
    print("ALL VISUAL TESTS DONE")

if __name__ == "__main__":
    run_test()

