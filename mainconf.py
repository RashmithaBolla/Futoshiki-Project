import pygame
import time
import random
import math

# Initialize Pygame
pygame.init()

import os
import sys

#dimensions of grid, window etc
grid_size = 4
cell_size = 80
gap_size = 15
width = grid_size * (cell_size + gap_size) + gap_size
height = grid_size * (cell_size + gap_size) + gap_size + 120
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Futoshiki Game")

#background image
image_path = os.path.join('images', 'futoback.jpg')

try:
    from pathlib import Path
    image_path = Path('images') / 'futoback.jpg'
    background_image = pygame.image.load(str(image_path)).convert()
    background_image = pygame.transform.scale(background_image, (width, height))
except Exception as e:
    print(f"Couldn't load background: {e}")
    background_image = None


# Colors
WHITE = (255, 255, 255)
LAVENDER = (230, 230, 250) #main heading
LIGHT_PURPLE = (250, 210, 250)  #headings
PURPLE = (100, 0, 100)  #status bar
PINK = (219, 112, 147) #numbers
LIGHT_PINK = (255, 210, 200)
LIGHT_GRAY = (220, 220, 220)
LIGHT_BLUE = (135, 206, 235)
GREEN = (0, 255, 0)  #if correct
RED = (255, 0, 0)  #if wrong
DARK_GRAY = (70, 70, 70)
BUTTON_HOVER = (200, 200, 200)
PALE_YELLOW = (255, 255, 224)  #button and square colours and inequalities
BLACK = (0, 0, 0)

# Confetti colors
CONFETTI_COLORS = [
    (255, 210, 200), (100, 0, 100), (230, 230, 250),
    (219, 112, 147), (255, 255, 224)
]

# Fonts
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 48)
symbol_font = pygame.font.Font(None, 32)
diff_font = pygame.font.Font(None, 30)
status_font = pygame.font.Font(None, 22)
title_font = pygame.font.Font(None, 48)

# Game levels with different initial grids and inequality constraints
levels = {
    "easy": {
        "initial_grid": [
            [0, 2, 0, 0],
            [0, 0, 0, 3],
            [1, 0, 4, 0],
            [0, 0, 0, 0]
        ],
        "horizontal_symbols": [
            [None, '>', None],
            [None, None, '<'],
            [None, '<', None],
            [None, None, None]
        ],
        "vertical_symbols": [
            [None, 'v', None, None],
            ['v', None, None, None],
            [None, None, None, None],
            [None, None, None, None]
        ],
        "solution": [
            [3, 2, 1, 4],
            [4, 1, 2, 3],
            [1, 3, 4, 2],
            [2, 4, 3, 1]
        ]
    },
    "medium": {
        "initial_grid": [
            [0, 0, 0, 2],
            [0, 0, 0, 0],
            [4, 0, 0, 0],
            [0, 0, 2, 0]
        ],
        "horizontal_symbols": [
            [None, '<', '>'],
            ['<', None, '<'],
            [None, '<', None],
            [None, '<', None]
        ],
        "vertical_symbols": [
            [None, None, 'v', None],
            ['^', None, None, None],
            [None, None, 'v', None],
            [None, None, None, None]
        ],
        "solution": [
            [2, 1, 4, 3],
            [3, 4, 1, 2],
            [4, 2, 3, 1],
            [1, 3, 2, 4]
        ]
    },
    "hard": {
        "initial_grid": [
            [0, 0, 0, 0],
            [0, 0, 0, 2],
            [2, 0, 0, 0],
            [4, 0, 0, 0]
        ],
        "horizontal_symbols": [
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, '>', None]
        ],
        "vertical_symbols": [
            [None, '^', None, None],
            [None, None, 'v', 'v'],
            [None, None, None, None],
            [None, None, None, None]
        ],
        "solution": [
            [3, 1, 2, 4],
            [1, 3, 4, 2],
            [2, 4, 3, 1],
            [4, 2, 1, 3]
        ]
    }
}


# Confetti particle class
class Confetti:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(5, 20)
        self.color = random.choice(CONFETTI_COLORS)
        self.speed = random.uniform(2, 5)
        self.angle = random.uniform(0, math.pi * 2)
        self.rotation = 0
        self.rotation_speed = random.uniform(-0.1, 0.1)
        self.shape = random.choice(["rectangle"])

    def update(self):
        self.x += math.cos(self.angle) * 2
        self.y += self.speed
        self.rotation += self.rotation_speed
        self.speed += 0.05  # Gravity effect

    def draw(self, surface):
        rotated = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

        if self.shape == "rectangle":
            pygame.draw.rect(rotated, self.color, (0, 0, self.size, self.size + 1200))

        if self.rotation != 0:
            rotated = pygame.transform.rotate(rotated, math.degrees(self.rotation))

        surface.blit(rotated, (self.x - rotated.get_width() // 2, self.y - rotated.get_height() // 2))


# Game state
current_level = None
game_grid = []
initial_grid = []
horizontal_symbols = []
vertical_symbols = []
solution_grid = []
start_time = 0
solved_time = None
selected_cell = None
show_level_selection = True
confetti_particles = []
confetti_start_time = None


def get_cell_rect(col, row):
    #Calculate cell rectangle with gap spacing
    x = gap_size + col * (cell_size + gap_size)
    y = gap_size + row * (cell_size + gap_size)
    return pygame.Rect(x, y, cell_size, cell_size)


def draw_symbol(surface, symbol, x, y):
    #Draw inequality symbol at specified position
    if symbol in ['>', '<', '^', 'v']:
        text = symbol_font.render(symbol, True, PALE_YELLOW )
        text_rect = text.get_rect(center=(x, y))
        surface.blit(text, text_rect)


def is_valid_move(grid, row, col, num):
#Check if placing num at (row, col) is valid
    # Check if the number already exists in row or column
    for i in range(grid_size):
        if (grid[row][i] == num and i != col) or (grid[i][col] == num and i != row):
            return False

    #Check horizontal constraints
    if col > 0 and horizontal_symbols[row][col - 1]:
        left_val = grid[row][col - 1]
        if left_val != 0:
            if horizontal_symbols[row][col - 1] == '>' and left_val <= num:
                return False
            if horizontal_symbols[row][col - 1] == '<' and left_val >= num:
                return False

    if col < grid_size - 1 and horizontal_symbols[row][col]:
        right_val = grid[row][col + 1]
        if right_val != 0:
            if horizontal_symbols[row][col] == '>' and num <= right_val:
                return False
            if horizontal_symbols[row][col] == '<' and num >= right_val:
                return False

    #Check vertical constraints
    if row > 0 and vertical_symbols[row - 1][col]:
        top_val = grid[row - 1][col]
        if top_val != 0:
            if vertical_symbols[row - 1][col] == '^' and top_val >= num:
                return False
            if vertical_symbols[row - 1][col] == 'v' and top_val <= num:
                return False

    if row < grid_size - 1 and vertical_symbols[row][col]:
        bottom_val = grid[row + 1][col]
        if bottom_val != 0:
            if vertical_symbols[row][col] == '^' and num >= bottom_val:
                return False
            if vertical_symbols[row][col] == 'v' and num <= bottom_val:
                return False

    return True


def is_puzzle_complete(grid):
    #Check if the puzzle is completely and correctly filled
    for row in range(grid_size):
        for col in range(grid_size):
            if grid[row][col] == 0:
                return False
            if not is_valid_move(grid, row, col, grid[row][col]):
                return False
    return True


def format_time(seconds):
    #Format time as mm:ss
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def draw_level_selection():
    #Draw background
    if background_image:
        screen.blit(background_image, (0, 0))

    title_text = title_font.render("Futoshiki Game", True, LIGHT_PURPLE)
    screen.blit(title_text, (width // 2 - title_text.get_width() // 2, 50))
    subtitle_text = diff_font.render("Select Difficulty Level", True, LIGHT_PINK)
    screen.blit(subtitle_text, (width // 2 - subtitle_text.get_width() // 2, 120))

    #Draw level buttons
    button_width = 200
    button_height = 60
    buttons = []
    for i, level in enumerate(["easy", "medium", "hard"]):
        button_rect = pygame.Rect(
            width // 2 - button_width // 2,
            180 + i * (button_height + 20),
            button_width,
            button_height
        )
        buttons.append((level, button_rect))
        mouse_pos = pygame.mouse.get_pos()
        color = BUTTON_HOVER if button_rect.collidepoint(mouse_pos) else PALE_YELLOW
        pygame.draw.rect(screen, color, button_rect, border_radius=10)
        pygame.draw.rect(screen, PINK, button_rect, 2, border_radius=10)
        level_text = font.render(level.capitalize(), True, PINK)
        screen.blit(level_text, (
            button_rect.centerx - level_text.get_width() // 2,
            button_rect.centery - level_text.get_height() // 2
        ))
    return buttons


def draw_game():
    global confetti_particles, confetti_start_time
    #Draw background
    if background_image:
        screen.blit(background_image, (0, 0))
    else:
        screen.fill(LAVENDER)

        #Create a semi-transparent overlay for the game area
        game_area_height = grid_size * (cell_size + gap_size) + gap_size
        overlay = pygame.Surface((width, game_area_height), pygame.SRCALPHA)
        overlay.fill((255, 255, 224, 180))
        screen.blit(overlay, (0, 0))

    #Draw grid and numbers
    for row in range(grid_size):
        for col in range(grid_size):
            rect = get_cell_rect(col, row)
            pygame.draw.rect(screen, PALE_YELLOW, rect)
            pygame.draw.rect(screen, PALE_YELLOW, rect, 3)
            value = game_grid[row][col]
            if value != 0:
                color = PINK if initial_grid[row][col] != 0 else PINK
                num_text = font.render(str(value), True, color)
                screen.blit(num_text, num_text.get_rect(center=rect.center))

    # Draw inequality symbols
    for row in range(grid_size):
        for col in range(grid_size - 1):
            if horizontal_symbols[row][col]:
                center_x = gap_size + col * (cell_size + gap_size) + cell_size + gap_size // 2
                center_y = gap_size + row * (cell_size + gap_size) + cell_size // 2
                draw_symbol(screen, horizontal_symbols[row][col], center_x, center_y)

    for col in range(grid_size):
        for row in range(grid_size - 1):
            if vertical_symbols[row][col]:
                center_x = gap_size + col * (cell_size + gap_size) + cell_size // 2
                center_y = gap_size + row * (cell_size + gap_size) + cell_size + gap_size // 2
                draw_symbol(screen, vertical_symbols[row][col], center_x, center_y)

    #Draw status bar
    status_rect = pygame.Rect(0, height - 60, width, 60)
    pygame.draw.rect(screen, PURPLE, status_rect)
    elapsed_time = time.time() - start_time
    time_text = status_font.render(f"Time: {format_time(elapsed_time)}", True, LIGHT_PURPLE)
    screen.blit(time_text, (20, height - 50))

    if is_puzzle_complete(game_grid):
        global solved_time
        if solved_time is None:
            solved_time = elapsed_time
            confetti_start_time = time.time()
            # Create initial confetti particles
            confetti_particles = []
            for _ in range(100):
                x = random.randint(0, width)
                y = random.randint(-50, -10)
                confetti_particles.append(Confetti(x, y))

        #Create the message
        message = f"Congratulations! Solved in {format_time(solved_time)}! Press R to restart"
        status_text = status_font.render(message, True, GREEN)

        #Calculate box dimensions and position (centered in grid area)
        text_width, text_height = status_text.get_size()
        box_width = text_width + 40
        box_height = text_height + 20
        grid_area_top = gap_size
        grid_area_height = grid_size * (cell_size + gap_size)

        box_x = width // 2 - box_width // 2
        box_y = grid_area_top + (grid_area_height - box_height) // 2

        #Draw the box with shadow effect
        pygame.draw.rect(screen, (200, 200, 200), (box_x + 3, box_y + 3, box_width, box_height))
        pygame.draw.rect(screen, PALE_YELLOW, (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, PINK, (box_x, box_y, box_width, box_height), 2)

        #Draw the text centered in the box
        screen.blit(status_text, (
            width // 2 - text_width // 2,
            box_y + (box_height - text_height) // 2
        ))

        #Update and draw confetti
        current_time = time.time()
        if current_time - confetti_start_time < 5:  #Show confetti for 5 seconds
            #Add new confetti
            if random.random() < 0.2:
                x = random.randint(0, width)
                y = random.randint(-50, -10)
                confetti_particles.append(Confetti(x, y))

            for particle in confetti_particles[:]:
                particle.update()
                particle.draw(screen)

                #Remove particles that are off screen
                if particle.y > height + 20:
                    confetti_particles.remove(particle)
        else:
            confetti_particles = []
    else:
        level_text = status_font.render(f"Level: {current_level.capitalize()}", True, LIGHT_PURPLE)
        screen.blit(level_text, (width - 130, height - 50))
        instruction_text = status_font.render("ESC: Menu | 1-4: Enter number | Del: Clear", True, LIGHT_PURPLE)
        screen.blit(instruction_text, (width // 2 - instruction_text.get_width() // 2, height - 30))


def reset_game(level):
    #Reset the game state for the specified level
    global game_grid, initial_grid, horizontal_symbols, vertical_symbols, solution_grid, start_time, solved_time, current_level, selected_cell, confetti_particles
    current_level = level
    initial_grid = [row[:] for row in levels[level]["initial_grid"]]
    game_grid = [row[:] for row in initial_grid]
    horizontal_symbols = [row[:] for row in levels[level]["horizontal_symbols"]]
    vertical_symbols = [row[:] for row in levels[level]["vertical_symbols"]]
    solution_grid = [row[:] for row in levels[level]["solution"]]
    start_time = time.time()
    solved_time = None
    selected_cell = None
    confetti_particles = []


#Main game loop
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if show_level_selection:
                buttons = draw_level_selection()
                pos = pygame.mouse.get_pos()
                for level, button_rect in buttons:
                    if button_rect.collidepoint(pos):
                        reset_game(level)
                        show_level_selection = False
            else:
                pos = pygame.mouse.get_pos()
                for row in range(grid_size):
                    for col in range(grid_size):
                        if get_cell_rect(col, row).collidepoint(pos):
                            selected_cell = (col, row)

        elif event.type == pygame.KEYDOWN:
            if not show_level_selection:
                if selected_cell:
                    col, row = selected_cell
                    if initial_grid[row][col] == 0:  # Only allow changes to empty cells
                        if pygame.K_1 <= event.key <= pygame.K_4:
                            num = event.key - pygame.K_0
                            game_grid[row][col] = num  # Allow any number to be placed temporarily
                            if not is_valid_move(game_grid, row, col, num):
                                game_grid[row][col] = 0  # Revert if invalid
                                pygame.draw.rect(screen, RED, get_cell_rect(col, row), 3)
                                pygame.display.flip()
                                pygame.time.delay(750)
                        elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                            game_grid[row][col] = 0
                    selected_cell = None
                elif event.key == pygame.K_r and is_puzzle_complete(game_grid):
                    show_level_selection = True
                elif event.key == pygame.K_ESCAPE:
                    show_level_selection = True
                elif event.key == pygame.K_h:  # Hint key
                    if selected_cell:
                        col, row = selected_cell
                        if initial_grid[row][col] == 0:
                            game_grid[row][col] = solution_grid[row][col]

    if show_level_selection:
        draw_level_selection()
    else:
        draw_game()
        if selected_cell:
            col, row = selected_cell
            pygame.draw.rect(screen, GREEN, get_cell_rect(col, row), 3)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()