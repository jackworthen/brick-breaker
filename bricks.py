import pygame
import random
import os
import time
import json
from pygame.locals import *

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Screen dimensions
SCREEN_WIDTH = 860
SCREEN_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
DARK_RED = (255, 175, 0)
PINK = (255, 192, 203)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 175, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
DARK_YELLOW = (175, 175, 0)
CYAN = (0, 178, 178)
DARK_CYAN = (0, 175, 175)
MAGENTA = (255, 0, 255)
DARK_MAGENTA = (175, 0, 175)
ORANGE = (255, 165, 0)
DARK_ORANGE = (175, 110, 0)
PURPLE = (128, 0, 128)
DARK_PURPLE = (64, 0, 64)
GREY = (169, 169, 169)

# Map each color to its dark version
DARK_COLOR_MAP = {
    WHITE: BLACK,
    RED: DARK_RED,
    GREEN: DARK_GREEN,
    YELLOW: DARK_YELLOW,
    CYAN: DARK_CYAN,
    MAGENTA: DARK_MAGENTA,
    ORANGE: DARK_ORANGE,
    PURPLE: DARK_PURPLE,
}

BRICK_COLORS = [GREEN, YELLOW, CYAN, MAGENTA, ORANGE, PURPLE]

# Paddle properties
PADDLE_BASE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_SPEED = 10
PADDLE_MAX_SPEED = 20
PADDLE_ACCELERATION = 1

# Ball properties
BALL_RADIUS = 10
BALL_SPEEDS = {1: 3, 2: 5, 3: 7}  # Different speeds for different difficulty levels

# Brick properties
BRICK_WIDTH = 75
BRICK_HEIGHT = 30
BRICK_PADDING = 10
BRICK_ROWS = 7
BRICK_COLUMNS = 10

# Power-up properties
POWER_UP_SIZE = 15
POWER_UP_SPEED = 5
EXPAND_POWER_UP_CHANCE = 0.05  
EXTRA_BALL_POWER_UP_CHANCE = 0.10  
ADDITIONAL_BRICKS_POWER_UP_CHANCE = 0.10  
REMOVE_BALLS_POWER_UP_CHANCE = 0.10  
SHOOTING_POWER_UP_CHANCE = 0.05  

# Initialize the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Brick Breaker")

# Clock for controlling the frame rate
clock = pygame.time.Clock()

# Load sounds
brick_hit_sound = pygame.mixer.Sound('media/audio/brick_hit.wav')
paddle_hit_sound = pygame.mixer.Sound('media/audio/paddle_hit.wav')
bonus_brick_sound = pygame.mixer.Sound('media/audio/bonus_brick.wav')

# Load music
splash_music = 'media/audio/splash.mp3'
game_over_music = 'media/audio/game_over.mp3'

# Load background images
bg_images = [os.path.join('media/bg', file) for file in os.listdir('media/bg') if file.endswith('.jpg')]

# Paddle class
class Paddle:
    def __init__(self, width):
        self.original_width = width
        self.rect = pygame.Rect((SCREEN_WIDTH // 2 - width // 2, SCREEN_HEIGHT - PADDLE_HEIGHT - 10),
                                (width, PADDLE_HEIGHT))
        self.base_speed = PADDLE_SPEED
        self.current_speed = PADDLE_SPEED
        self.shooting_power = False
        self.balls_to_shoot = 0

    def move(self, direction):
        if direction == 'left' and self.rect.left > 0:
            self.rect.x -= self.current_speed
            if self.rect.left < 0:
                self.rect.left = 0
        elif direction == 'right' and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.current_speed
            if self.rect.right > SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH

    def accelerate(self):
        if self.current_speed < PADDLE_MAX_SPEED:
            self.current_speed += PADDLE_ACCELERATION

    def reset_speed(self):
        self.current_speed = self.base_speed

    def draw(self, screen, score):
        pygame.draw.rect(screen, BLUE, self.rect)
        self.draw_score(screen, score)

        # Draw white tips
        tip_width = 5
        pygame.draw.rect(screen, WHITE, (self.rect.left, self.rect.top, tip_width, PADDLE_HEIGHT))
        pygame.draw.rect(screen, WHITE, (self.rect.right - tip_width, self.rect.top, tip_width, PADDLE_HEIGHT))

    def draw_score(self, screen, score):
        font = pygame.font.Font(None, 36)
        score_text = font.render(str(score), True, WHITE)
        text_rect = score_text.get_rect(center=self.rect.center)
        screen.blit(score_text, text_rect)

    def expand(self):
        self.rect.width = int(self.rect.width * 1.25)

    def reset_size(self):
        self.rect.width = self.original_width

    def reset_size_based_on_difficulty(self, difficulty):
        self.original_width = PADDLE_BASE_WIDTH - (difficulty - 2) * 20
        self.reset_size()

    def enable_shooting(self):
        self.shooting_power = True
        self.balls_to_shoot = 5

# Ball class
class Ball:
    def __init__(self, speed, x=None, y=None):
        self.rect = pygame.Rect((SCREEN_WIDTH // 2 - BALL_RADIUS if x is None else x,
                                 SCREEN_HEIGHT // 2 - BALL_RADIUS if y is None else y),
                                (BALL_RADIUS * 2, BALL_RADIUS * 2))
        self.dx = speed * random.choice([-1, 1])
        self.dy = -speed
        self.attached = True
        self.speed = speed

    def reset(self, paddle):
        self.rect = pygame.Rect((paddle.rect.centerx - BALL_RADIUS, paddle.rect.top - BALL_RADIUS * 2),
                                (BALL_RADIUS * 2, BALL_RADIUS * 2))
        self.dx = self.speed * random.choice([-1, 1])
        self.dy = -self.speed
        self.attached = True

    def move(self):
        if not self.attached:
            self.rect.x += self.dx
            self.rect.y += self.dy

    def bounce(self, axis):
        if axis == 'x':
            self.dx = -self.dx
        elif axis == 'y':
            self.dy = -self.dy

    def bounce_off_paddle(self, paddle):
        hit_pos = (self.rect.centerx - paddle.rect.left) / paddle.rect.width
        self.dx = (hit_pos - 0.5) * 2 * self.speed  # Adjust the ball's horizontal velocity
        self.dy = -abs(self.dy)  # Ensure the ball bounces upwards

        # Ensure the ball's velocity doesn't exceed a reasonable limit
        max_speed = self.speed * 1.5
        if abs(self.dx) > max_speed:
            self.dx = max_speed if self.dx > 0 else -max_speed

    def draw(self, screen):
        pygame.draw.circle(screen, RED, (self.rect.x + BALL_RADIUS, self.rect.y + BALL_RADIUS), BALL_RADIUS)

# Power-up class
class PowerUp:
    def __init__(self, x, y, power_up_type):
        self.rect = pygame.Rect(x, y, POWER_UP_SIZE, POWER_UP_SIZE)
        self.type = power_up_type  # 'expand', 'extra_ball', 'additional_bricks', 'remove_balls', or 'shooting'
        self.active = True

    def move(self):
        self.rect.y += POWER_UP_SPEED

    def draw(self, screen):
        if self.type == 'expand':
            color = BLUE
        elif self.type == 'extra_ball':
            color = ORANGE
        elif self.type == 'additional_bricks':
            color = WHITE
        elif self.type == 'remove_balls':
            color = PURPLE
        elif self.type == 'shooting':
            color = BLACK
        pygame.draw.rect(screen, color, self.rect)

# Brick class
class Brick:
    def __init__(self, x, y, color, requires_two_hits, flashing=False):
        self.rect = pygame.Rect((x, y), (BRICK_WIDTH, BRICK_HEIGHT))
        self.color = color
        self.requires_two_hits = requires_two_hits
        self.hit = False
        self.flashing = flashing
        self.flash_timer = 0
        self.flash_interval = 500  # Flash every 500ms

        power_up_type = None
        if random.random() < EXPAND_POWER_UP_CHANCE:
            power_up_type = 'expand'
        elif random.random() < EXTRA_BALL_POWER_UP_CHANCE:
            power_up_type = 'extra_ball'
        elif random.random() < ADDITIONAL_BRICKS_POWER_UP_CHANCE:
            power_up_type = 'additional_bricks'
        elif random.random() < REMOVE_BALLS_POWER_UP_CHANCE:
            power_up_type = 'remove_balls'
        elif random.random() < SHOOTING_POWER_UP_CHANCE:
            power_up_type = 'shooting'
        self.power_up = PowerUp(x + BRICK_WIDTH // 2 - POWER_UP_SIZE // 2, y, power_up_type) if power_up_type else None

    def draw(self, screen):
        if self.flashing:
            current_time = pygame.time.get_ticks()
            if current_time - self.flash_timer > self.flash_interval:
                self.flash_timer = current_time
                self.color = RED if self.color == WHITE else WHITE
        pygame.draw.rect(screen, self.color, self.rect)

    def hit_brick(self):
        if self.requires_two_hits:
            if not self.hit:
                self.hit = True
                self.color = DARK_COLOR_MAP[self.color]  # Change to cracked appearance
            else:
                return True  # Brick is destroyed
        else:
            return True  # Brick is destroyed

# Create bricks
def create_bricks(color):
    bricks = []
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLUMNS):
            x = col * (BRICK_WIDTH + BRICK_PADDING) + BRICK_PADDING
            y = row * (BRICK_HEIGHT + BRICK_PADDING) + BRICK_PADDING
            requires_two_hits = random.choice([True, False])  # Randomly assign bricks to require two hits
            bricks.append(Brick(x, y, color, requires_two_hits))
    return bricks

# Create flashing bricks without overlapping existing bricks
def create_flashing_bricks(count, existing_bricks):
    bricks = []
    attempts = 0
    while len(bricks) < count and attempts < 1000:  # Limit attempts to prevent infinite loop
        x = random.randint(0, SCREEN_WIDTH - BRICK_WIDTH)
        y = random.randint(BRICK_ROWS * (BRICK_HEIGHT + BRICK_PADDING) + BRICK_PADDING, SCREEN_HEIGHT - BRICK_HEIGHT)
        new_brick = Brick(x, y, WHITE, True, flashing=True)
        overlap = False
        for brick in existing_bricks + bricks:
            if new_brick.rect.colliderect(brick.rect):
                overlap = True
                break
        if not overlap:
            bricks.append(new_brick)
        attempts += 1
    return bricks

def create_additional_bricks(count, existing_bricks, current_color):
    bricks = []
    attempts = 0
    new_color = random.choice([color for color in BRICK_COLORS if color != current_color])
    while len(bricks) < count and attempts < 1000:  # Limit attempts to prevent infinite loop
        x = random.randint(0, SCREEN_WIDTH - BRICK_WIDTH)
        y = random.randint(BRICK_ROWS * (BRICK_HEIGHT + BRICK_PADDING) + BRICK_PADDING, SCREEN_HEIGHT - BRICK_HEIGHT)
        new_brick = Brick(x, y, new_color, False)
        overlap = False
        for brick in existing_bricks + bricks:
            if new_brick.rect.colliderect(brick.rect):
                overlap = True
                break
        if not overlap:
            bricks.append(new_brick)
        attempts += 1
    return bricks

def find_highest_ball(balls):
    highest_ball = balls[0]
    for ball in balls:
        if ball.rect.top < highest_ball.rect.top:
            highest_ball = ball
    return highest_ball

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes} min {seconds} sec"

# Function to save the score
def save_score(initials, score, total_time, difficulty):
    score_data = {
        "initials": initials,
        "score": score,
        "total_time": format_time(total_time),
        "difficulty": difficulty
    }
    if os.path.exists("scores.json"):
        with open("scores.json", "r") as file:
            data = json.load(file)
    else:
        data = []
    data.append(score_data)
    with open("scores.json", "w") as file:
        json.dump(data, file, indent=4)

# Function to load high scores for a specific difficulty
def load_high_scores(difficulty):
    if os.path.exists("scores.json"):
        with open("scores.json", "r") as file:
            data = json.load(file)
            return sorted([entry for entry in data if entry["difficulty"] == difficulty], key=lambda x: x["score"], reverse=True)[:10]
    return []

# Main game loop
def main():
    def new_game(level=0, difficulty=2):
        color = BRICK_COLORS[level % len(BRICK_COLORS)]
        global CRACKED_COLOR
        CRACKED_COLOR = DARK_COLOR_MAP[color]  # Set cracked color based on the brick color
        paddle_width = PADDLE_BASE_WIDTH - (difficulty - 2) * 20  # Adjust the paddle size based on difficulty
        paddle = Paddle(paddle_width)
        ball = Ball(BALL_SPEEDS[difficulty])
        ball.reset(paddle)
        background_image = pygame.image.load(random.choice(bg_images))
        background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        return paddle, [ball], create_bricks(color), 0, level, difficulty, [], background_image

    paddle, balls, bricks, score, level, difficulty, power_ups, background_image = None, None, None, 0, 0, 2, [], None
    running = True
    game_over = False
    paused = False
    splash_screen = True
    waiting_to_start = False
    choosing_difficulty = True
    level_complete = False

    # Timer variables
    total_time = 0
    level_start_time = 0

    splash_text_colors = [RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, ORANGE, PURPLE]
    splash_text_index = 0
    splash_text_timer = 0
    splash_text_interval = 500  # Time in milliseconds between color changes

    high_scores_text_colors = [RED, WHITE]
    high_scores_text_index = 0
    high_scores_text_timer = 0
    high_scores_text_interval = 500  # Time in milliseconds between color changes

    # Flashing text properties
    flash_text_colors = [WHITE, RED]
    flash_text_index = 0
    flash_text_timer = 0
    flash_text_interval = 500  # Time in milliseconds between color changes

    # Stationary text properties
    font = pygame.font.Font(None, 74)
    text_x, text_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50

    left_pressed = False
    right_pressed = False

    # Play splash screen music
    pygame.mixer.music.load(splash_music)
    pygame.mixer.music.play(-1)

    # Load the splash image
    splash_image = pygame.image.load('media/splash.jpg')
    splash_image = pygame.transform.scale(splash_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    high_scores = []

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused
                if game_over and event.key == pygame.K_RETURN:
                    splash_screen = True
                    choosing_difficulty = True
                    pygame.mixer.music.load(splash_music)
                    pygame.mixer.music.play(-1)
                    game_over = False
                if splash_screen and choosing_difficulty:
                    if event.key == pygame.K_1:
                        difficulty = 1
                        choosing_difficulty = False
                        high_scores = load_high_scores(difficulty)
                        paddle, balls, bricks, score, level, difficulty, power_ups, background_image = new_game(difficulty=difficulty)
                    elif event.key == pygame.K_2:
                        difficulty = 2
                        choosing_difficulty = False
                        high_scores = load_high_scores(difficulty)
                        paddle, balls, bricks, score, level, difficulty, power_ups, background_image = new_game(difficulty=difficulty)
                    elif event.key == pygame.K_3:
                        difficulty = 3
                        choosing_difficulty = False
                        high_scores = load_high_scores(difficulty)
                        paddle, balls, bricks, score, level, difficulty, power_ups, background_image = new_game(difficulty=difficulty)
                if splash_screen and event.key == pygame.K_RETURN and not choosing_difficulty:
                    splash_screen = False
                    waiting_to_start = True  # Set to wait for user to start game
                if waiting_to_start and event.key == pygame.K_RETURN:
                    waiting_to_start = False  # Start the game
                    for ball in balls:
                        ball.attached = False

                    # Reset paddle control states
                    left_pressed = False
                    right_pressed = False

                    # Stop splash music
                    pygame.mixer.music.stop()

                    # Start the timer for the level
                    level_start_time = time.time()

                if level_complete and event.key == pygame.K_RETURN:
                    level_complete = False
                    paddle.reset_size()  # Reset paddle size at the end of the level
                    ball = Ball(BALL_SPEEDS[difficulty])
                    ball.reset(paddle)
                    ball.attached = False  # Ensure the ball moves immediately
                    balls = [ball]
                    bricks = create_bricks(BRICK_COLORS[level % len(BRICK_COLORS)])
                    power_ups = []  # Clear any remaining power-ups
                    background_image = pygame.image.load(random.choice(bg_images))
                    background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

                    # Start the timer for the next level
                    level_start_time = time.time()

                if event.key == pygame.K_LEFT:
                    left_pressed = True
                if event.key == pygame.K_RIGHT:
                    right_pressed = True
                if event.key == pygame.K_SPACE and paddle.shooting_power and paddle.balls_to_shoot > 0:
                    new_ball = Ball(BALL_SPEEDS[difficulty], paddle.rect.centerx - BALL_RADIUS, paddle.rect.top - BALL_RADIUS * 2)
                    new_ball.bounce_off_paddle(paddle)
                    new_ball.attached = False
                    balls.append(new_ball)
                    paddle.balls_to_shoot -= 1
                    if paddle.balls_to_shoot == 0:
                        paddle.shooting_power = False

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    left_pressed = False
                    paddle.reset_speed()
                if event.key == pygame.K_RIGHT:
                    right_pressed = False
                    paddle.reset_speed()

        keys = pygame.key.get_pressed()
        if not game_over and not paused and not splash_screen and not waiting_to_start and not level_complete:
            if left_pressed:
                paddle.accelerate()
                paddle.move('left')
            if right_pressed:
                paddle.accelerate()
                paddle.move('right')

            for ball in balls:
                if ball.attached:
                    ball.rect.x = paddle.rect.centerx - BALL_RADIUS
                    ball.rect.y = paddle.rect.top - BALL_RADIUS * 2
                else:
                    ball.move()

                # Ball collision with walls
                if ball.rect.left <= 0:
                    ball.rect.left = 0
                    ball.bounce('x')
                if ball.rect.right >= SCREEN_WIDTH:
                    ball.rect.right = SCREEN_WIDTH - ball.rect.width
                    ball.bounce('x')
                if ball.rect.top <= 0:
                    ball.rect.top = 0
                    ball.bounce('y')

                # Ball collision with paddle
                if ball.rect.colliderect(paddle.rect) and not ball.attached:
                    ball.bounce_off_paddle(paddle)
                    paddle_hit_sound.play()

                # Ball collision with bricks
                for brick in bricks[:]:
                    if ball.rect.colliderect(brick.rect):
                        ball.bounce('y')
                        brick_hit_sound.play()
                        score += 1  # Score 1 point for each brick broken
                        if brick.hit_brick():
                            if (brick.power_up):
                                power_ups.append(brick.power_up)
                                bonus_brick_sound.play()  # Play bonus sound when power-up brick is hit
                            bricks.remove(brick)

            # Move power-ups
            for power_up in power_ups[:]:
                power_up.move()
                if power_up.rect.colliderect(paddle.rect):
                    if power_up.type == 'expand':
                        paddle.expand()
                    elif power_up.type == 'extra_ball':
                        new_ball = Ball(BALL_SPEEDS[difficulty], paddle.rect.centerx - BALL_RADIUS, paddle.rect.top - BALL_RADIUS * 2)
                        new_ball.bounce_off_paddle(paddle)
                        new_ball.attached = False
                        balls.append(new_ball)
                    elif power_up.type == 'additional_bricks':
                        new_bricks = create_flashing_bricks(5, bricks)
                        bricks.extend(new_bricks)
                    elif power_up.type == 'remove_balls':
                        if len(balls) > 1:
                            highest_ball = find_highest_ball(balls)
                            balls = [highest_ball]
                        else:
                            new_bricks = create_additional_bricks(3, bricks, BRICK_COLORS[level % len(BRICK_COLORS)])
                            bricks.extend(new_bricks)
                        paddle.reset_size_based_on_difficulty(difficulty)
                    elif power_up.type == 'shooting':
                        paddle.enable_shooting()
                    power_ups.remove(power_up)
                elif power_up.rect.top >= SCREEN_HEIGHT:
                    power_ups.remove(power_up)

            # Remove balls that fall below the screen
            balls = [ball for ball in balls if ball.rect.top < SCREEN_HEIGHT]

            # Check if all balls are lost
            if not balls:
                game_over = True
                pygame.mixer.music.load(game_over_music)
                pygame.mixer.music.play()

                # Stop the timer and calculate total time
                total_time += time.time() - level_start_time

            # Check if all bricks are destroyed
            if not bricks:
                level_complete = True
                level += 1

                # Stop the timer and calculate total time
                total_time += time.time() - level_start_time

        screen.fill(BLACK)

        if splash_screen:
            screen.blit(splash_image, (0, 0))  # Draw the splash image

            current_time = pygame.time.get_ticks()
            if current_time - splash_text_timer > splash_text_interval:
                splash_text_timer = current_time
                splash_text_index = (splash_text_index + 1) % len(splash_text_colors)

            if current_time - high_scores_text_timer > high_scores_text_interval:
                high_scores_text_timer = current_time
                high_scores_text_index = (high_scores_text_index + 1) % len(high_scores_text_colors)

            font = pygame.font.Font(None, 74)
            text_color = splash_text_colors[splash_text_index]
            text = font.render("", True, text_color)
            screen.blit(text, (text_x - text.get_width() // 2, text_y - text.get_height() // 2))
            font = pygame.font.Font(None, 36)
            current_time = pygame.time.get_ticks()
            if current_time - flash_text_timer > flash_text_interval:
                flash_text_timer = current_time
                flash_text_index = (flash_text_index + 1) % len(flash_text_colors)
                
            flash_text_color = flash_text_colors[flash_text_index]
            if choosing_difficulty:
                text = font.render("Choose Difficulty: 1 - 3", True, flash_text_color)
                screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT - 475))
            else:
                text = font.render("Press Enter to Start", True, flash_text_color)
                screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT - 475))

                # Display top 10 high scores for the selected difficulty
                high_scores_text = "- High Scores -"
                high_scores_rendered = font.render(high_scores_text, True, high_scores_text_colors[high_scores_text_index])
                screen.blit(high_scores_rendered, (SCREEN_WIDTH // 2 - high_scores_rendered.get_width() // 2, SCREEN_HEIGHT - 425))
                for i, score_entry in enumerate(high_scores):
                    score_text = f"{i + 1}. {score_entry['initials']} - {score_entry['score']} - {score_entry['total_time']}"
                    score_rendered = font.render(score_text, True, high_scores_text_colors[high_scores_text_index])
                    screen.blit(score_rendered, (SCREEN_WIDTH // 2 - score_rendered.get_width() // 2, SCREEN_HEIGHT - 400 + i * 25))
        elif not game_over:
            if not level_complete:
                screen.blit(background_image, (0, 0))  # Draw the background image
            paddle.draw(screen, score)
            for ball in balls:
                ball.draw(screen)
            for brick in bricks:
                brick.draw(screen)
            for power_up in power_ups:
                power_up.draw(screen)
            if paused:
                font = pygame.font.Font(None, 74)
                text = font.render("- PAUSED -", True, BLUE)
                screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - text.get_height() // 2))
            elif level_complete:
                font = pygame.font.Font(None, 74)
                text = font.render(f"Level {level} Complete!", True, WHITE)
                screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - text.get_height() // 2))
                font = pygame.font.Font(None, 36)
                text = font.render("Press Enter to Start Next Level", True, WHITE)
                screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 + text.get_height()))
                
                # Display total time
                total_time_text = font.render(f"Total Time: {format_time(total_time)}", True, WHITE)
                screen.blit(total_time_text, (SCREEN_WIDTH // 2 - total_time_text.get_width() // 2, SCREEN_HEIGHT // 2 + 2 * text.get_height()))
        else:
            font = pygame.font.Font(None, 74)
            text = font.render("Game Over", True, RED)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - text.get_height() // 2))
            font = pygame.font.Font(None, 36)
            score_text = font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 + score_text.get_height()))
          
           # Display total time
            total_time_text = font.render(f"Time: {format_time(total_time)}", True, WHITE)
            screen.blit(total_time_text, (SCREEN_WIDTH // 2 - total_time_text.get_width() // 2, SCREEN_HEIGHT // 2 + 3 * text.get_height()))
            
            # Ask the user if they want to save their score
            font = pygame.font.Font(None, 36)
            text = font.render("Save score? (Y/N)", True, WHITE)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 + 4 * text.get_height()))

            pygame.display.flip()
            
            while True:
                event = pygame.event.wait()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        initials = ""
                        save_dialog = True
                        while save_dialog:
                            for e in pygame.event.get():
                                if e.type == pygame.KEYDOWN:
                                    if e.key == pygame.K_RETURN:
                                        save_dialog = False
                                    elif e.key == pygame.K_BACKSPACE:
                                        initials = initials[:-1]
                                    else:
                                        initials += e.unicode
                            screen.fill(BLACK)
                            text = font.render("Enter your initials: " + initials, True, WHITE)
                            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2))
                            pygame.display.flip()
                        save_score(initials, score, total_time, difficulty)
                        splash_screen = True
                        choosing_difficulty = True
                        pygame.mixer.music.load(splash_music)
                        pygame.mixer.music.play(-1)
                        game_over = False
                        break
                    elif event.key == pygame.K_n:
                        splash_screen = True
                        choosing_difficulty = True
                        pygame.mixer.music.load(splash_music)
                        pygame.mixer.music.play(-1)
                        game_over = False
                        break
            text = font.render("Press Enter", True, WHITE)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 + 5 * text.get_height()))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
