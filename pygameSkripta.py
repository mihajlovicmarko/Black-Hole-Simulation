import pygame
import sys
import pickle
import matplotlib.pyplot as plt
import numpy as np


def KartezijskeKoordinate(r, theta, xProzora = 1000, yProzora = 1000):
    X = np.multiply(np.cos(theta), r) * 10 + xProzora / 2
    Y = np.multiply(np.sin(theta), r) * 10 + yProzora / 2
    return X, Y
# Initialize Pygame
pygame.init()

# Set up the window
width, height = 1000, 1000
window = pygame.display.set_mode((width, height))
pygame.display.set_caption("Moving Dot")

dot_radius = 10

dot_radius1 = 20
dot_color = (100, 100, 100)
dot_color1 = (0, 0, 0)

dot_x = width // 2
dot_y = height // 2
dot_speed = 5
with open("ugao", "br") as f:
    ugao = pickle.load(f)
with open("precnik", "br") as f:
    precnik = pickle.load(f)

x, y = KartezijskeKoordinate(precnik, ugao)
print(x[0], y[0])
t = 0
while True:
    t += 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Move the dot
    

    # Update the window
    window.fill((255, 255, 255))  # White background
    pygame.draw.circle(window, dot_color, (x[t], y[t]), 10)
    pygame.draw.circle(window, dot_color1, (500, 500), 20)

    pygame.display.flip()

    # Control the frame rate
    pygame.time.Clock().tick(60)

