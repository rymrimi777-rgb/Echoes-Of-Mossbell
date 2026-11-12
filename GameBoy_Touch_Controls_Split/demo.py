"""Quick demo: python demo.py  (mouse click or touch the buttons)."""
import pygame

from gb_controls import GB_BUTTON_DOWN, GB_BUTTON_UP, build_default_controller

SIZE = (640, 360)

pygame.init()
screen = pygame.display.set_mode(SIZE)  # must exist before building the controller
pygame.display.set_caption("GameBoy Touch Controls demo")
font = pygame.font.Font(None, 28)
clock = pygame.time.Clock()
controller = build_default_controller(SIZE, scale=3, with_xy=True)

running = True
while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == GB_BUTTON_DOWN:
            print("down:", event.action)
        elif event.type == GB_BUTTON_UP:
            print("up:  ", event.action)
        controller.handle_event(event, SIZE)

    controller.update(dt)
    screen.fill((15, 56, 15))
    held = [b.action for b in controller.buttons if b.pressed]
    screen.blit(font.render("held: " + (", ".join(held) or "-"), True, (155, 188, 15)), (16, 16))
    controller.draw(screen)
    pygame.display.flip()

pygame.quit()
