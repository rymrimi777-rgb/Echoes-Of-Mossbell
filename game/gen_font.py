"""Generate a bitmap font sheet for pixel-perfect text."""
import pygame
import os

pygame.init()

CHARS = (' !"#$%&\'()*+,-./0123456789:;<=>?@'
         'ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`'
         'abcdefghijklmnopqrstuvwxyz{|}~')

font = pygame.font.Font(None, 16)
char_w = 6
char_h = 8
sheet_w = len(CHARS) * char_w

sheet = pygame.Surface((sheet_w, char_h))
sheet.fill((155, 188, 15))
sheet.set_colorkey((155, 188, 15))

for i, ch in enumerate(CHARS):
    s = font.render(ch, False, (15, 56, 15))
    sheet.blit(s, (i * char_w, 0))

out = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                   "assets", "fonts", "font_6x8.png")
pygame.image.save(sheet, out)
print(f"Font sheet saved: {sheet_w}x{char_h}, {len(CHARS)} chars -> {out}")
pygame.quit()

