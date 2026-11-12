import pygame

pygame.init()
pygame.display.set_mode((160, 144))

f_dialogue = pygame.font.Font("assets/fonts/PixelOperator.ttf", 16)
f_dialogue_sm = pygame.font.Font("assets/fonts/PixelOperator.ttf", 14)
f_speaker = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 6)

print("Dialogue font line height:", f_dialogue.get_linesize())
print("Dialogue sm font line height:", f_dialogue_sm.get_linesize())
print("Speaker font height:", f_speaker.get_height())

# Test text width with portrait (max_w = 110 px)
text = "Welcome, child. Dark times have come to Mossbell."
words = text.split()
line1 = ""
for w in words:
    test = (line1 + " " + w).strip()
    if f_dialogue.size(test)[0] <= 110:
        line1 = test
    else:
        break
print("Line 1 with portrait:", f"'{line1}'", f_dialogue.size(line1))

pygame.quit()
