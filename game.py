"""A small Pygame air-hockey prototype for Stage 1."""

import math
import random

import pygame

from config import (
    BACKGROUND_COLOR,
    FPS,
    LINE_COLOR,
    PADDLE_RADIUS,
    PLAYER_COLOR,
    PUCK_COLOR,
    PUCK_RADIUS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TABLE_COLOR,
    TABLE_MARGIN,
    TEXT_COLOR,
)


def draw_table(screen):
    """Draw the rink markings."""
    screen.fill(BACKGROUND_COLOR)
    rink = pygame.Rect(
        TABLE_MARGIN,
        TABLE_MARGIN,
        SCREEN_WIDTH - TABLE_MARGIN * 2,
        SCREEN_HEIGHT - TABLE_MARGIN * 2,
    )
    pygame.draw.rect(screen, TABLE_COLOR, rink, border_radius=18)
    pygame.draw.rect(screen, LINE_COLOR, rink, width=3, border_radius=18)

    pygame.draw.line(
        screen, LINE_COLOR,
        (TABLE_MARGIN, SCREEN_HEIGHT // 2),
        (SCREEN_WIDTH - TABLE_MARGIN, SCREEN_HEIGHT // 2),
        2,
    )
    pygame.draw.circle(screen, LINE_COLOR, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 72, 2)

def reset_puck():
    """Put the puck in the center with a small random starting direction."""
    start_x = SCREEN_WIDTH / 2
    start_y = SCREEN_HEIGHT / 2
    direction_x = random.choice((-1, 1))
    direction_y = random.choice((-1, 1))
    return start_x, start_y, direction_x * 250.0, direction_y * 180.0


def keep_player_on_own_half(x, y):
    """Keep the player's paddle inside the lower half of the rink."""
    left = TABLE_MARGIN + PADDLE_RADIUS
    right = SCREEN_WIDTH - TABLE_MARGIN - PADDLE_RADIUS
    top = SCREEN_HEIGHT / 2 + PADDLE_RADIUS + 2
    bottom = SCREEN_HEIGHT - TABLE_MARGIN - PADDLE_RADIUS
    return max(left, min(right, x)), max(top, min(bottom, y))


def bounce_puck_off_player(puck_x, puck_y, puck_vx, puck_vy, player_x, player_y):
    """Resolve a circle-to-circle collision with the player paddle."""
    difference_x = puck_x - player_x
    difference_y = puck_y - player_y
    distance = math.hypot(difference_x, difference_y)
    minimum_distance = PUCK_RADIUS + PADDLE_RADIUS

    if distance == 0:
        difference_x, difference_y = 0, -1
        distance = 1

    if distance >= minimum_distance:
        return puck_x, puck_y, puck_vx, puck_vy

    normal_x = difference_x / distance
    normal_y = difference_y / distance

    # Move the puck just outside the paddle so it cannot get stuck inside it.
    overlap = minimum_distance - distance
    puck_x += normal_x * overlap
    puck_y += normal_y * overlap

    # Reflect only if the puck is moving into the paddle.
    speed_toward_paddle = puck_vx * normal_x + puck_vy * normal_y
    if speed_toward_paddle < 0:
        puck_vx -= 2 * speed_toward_paddle * normal_x
        puck_vy -= 2 * speed_toward_paddle * normal_y

    # A little extra speed makes paddle hits feel responsive.
    puck_vx *= 1.04
    puck_vy *= 1.04
    return puck_x, puck_y, puck_vx, puck_vy


def run_game():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Webcam Air Hockey — Stage 1")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)

    player_x = SCREEN_WIDTH / 2
    player_y = SCREEN_HEIGHT - TABLE_MARGIN - 70
    puck_x, puck_y, puck_vx, puck_vy = reset_puck()
    running = True
    paused = False

    while running:
        # dt keeps movement consistent across computers with different FPS.
        dt = min(clock.tick(FPS) / 1000.0, 0.03)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    puck_x, puck_y, puck_vx, puck_vy = reset_puck()

        keys = pygame.key.get_pressed()
        move_x = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(
            keys[pygame.K_LEFT] or keys[pygame.K_a]
        )
        move_y = int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(
            keys[pygame.K_UP] or keys[pygame.K_w]
        )

        if move_x or move_y:
            # Keyboard is useful for testing; mouse control remains available.
            keyboard_speed = 440
            player_x += move_x * keyboard_speed * dt
            player_y += move_y * keyboard_speed * dt
        else:
            player_x, player_y = pygame.mouse.get_pos()

        player_x, player_y = keep_player_on_own_half(player_x, player_y)

        if not paused:
            puck_x += puck_vx * dt
            puck_y += puck_vy * dt

            left_wall = TABLE_MARGIN + PUCK_RADIUS
            right_wall = SCREEN_WIDTH - TABLE_MARGIN - PUCK_RADIUS
            top_wall = TABLE_MARGIN + PUCK_RADIUS
            bottom_wall = SCREEN_HEIGHT - TABLE_MARGIN - PUCK_RADIUS

            if puck_x < left_wall:
                puck_x = left_wall
                puck_vx = abs(puck_vx)
            elif puck_x > right_wall:
                puck_x = right_wall
                puck_vx = -abs(puck_vx)

            if puck_y < top_wall:
                puck_y = top_wall
                puck_vy = abs(puck_vy)
            elif puck_y > bottom_wall:
                puck_y = bottom_wall
                puck_vy = -abs(puck_vy)

            puck_x, puck_y, puck_vx, puck_vy = bounce_puck_off_player(
                puck_x, puck_y, puck_vx, puck_vy, player_x, player_y
            )

        draw_table(screen)
        pygame.draw.circle(screen, PLAYER_COLOR, (round(player_x), round(player_y)), PADDLE_RADIUS)
        pygame.draw.circle(screen, PUCK_COLOR, (round(puck_x), round(puck_y)), PUCK_RADIUS)
        pygame.draw.circle(screen, (48, 80, 87), (round(puck_x), round(puck_y)), 5)

        instruction = font.render("Move the mouse or use WASD / arrow keys", True, TEXT_COLOR)
        screen.blit(instruction, (TABLE_MARGIN + 18, 16))
        help_text = small_font.render("SPACE: pause   R: reset puck   ESC: quit", True, TEXT_COLOR)
        screen.blit(help_text, (TABLE_MARGIN + 18, SCREEN_HEIGHT - 32))

        if paused:
            pause_text = font.render("PAUSED — press SPACE to continue", True, TEXT_COLOR)
            screen.blit(pause_text, pause_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)))

        pygame.display.flip()

    pygame.quit()