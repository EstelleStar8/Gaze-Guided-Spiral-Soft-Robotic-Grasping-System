
# =============== Just doing pygame testing in here, this file is currently irrelevant ========================

import pygame

pygame.init()
screen = pygame.display.set_mode((640,640))
clock = pygame.time.Clock()
delta_time = 0.1

# Load in pyGame assets
calibrateButton = pygame.image.load('placeholderCalibrate.png').convert()   

running = True
while running:
    # Checks for all events (button presses and the like)
    event = pygame.event.poll()
    if event.type == pygame.quit:
        running = False

    # Basically clears the screen every frame so you don't get bleeding images
    screen.fill((255,0,255))

    # Render button
    # calibrateButton = pygame.transform.scale(calibrateButton, 
    #                                         (calibrateButton.get_width() * 0.5,
    #                                         calibrateButton.get_height() * 0.5))

    screen.blit(calibrateButton, (200,200))

    pygame.display.flip()

    # Normalize time to not be dependant on framerate
    delta_time = clock.tick(60)
    delta_time = max(0.001, min(0.1, delta_time))
