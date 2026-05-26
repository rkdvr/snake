"""
theme.py — Shared visual constants and drawing functions.

Any module that renders the snake or food should import from here so that
visual changes only need to be made in one place.

Shared between
--------------
    snake_pygame.py   — playable game
    snake_solver.py   — AI solver visualiser

Not shared
----------
    Grid drawing, HUD, and overlay rendering differ between the two games
    and stay in their respective files.

Importing
---------
    from theme import (
        C_BG, C_HEAD, C_BODY_A, C_FOOD, C_FOOD_SPOT,
        C_TEXT, C_MUTED, C_OVERLAY, C_GRID,
        draw_snake, draw_food,
    )
"""

import math
import pygame

from constants import CELL

# ── Shared colour palette ─────────────────────────────────────────────────────

C_BG        = (13,  17,  23)
C_HEAD      = (88, 166, 255)
C_BODY_A    = (35, 134,  54)
C_BODY_B    = (25,  97,  39)   # kept for reference; not used in rendering
C_FOOD      = (248, 81,  73)
C_FOOD_SPOT = (255, 123, 114)
C_TEXT      = (230, 237, 243)
C_MUTED     = (139, 148, 158)
C_OVERLAY   = (13,  17,  23, 210)
C_GRID      = (30,  35,  42)


# ── Shared drawing functions ──────────────────────────────────────────────────

def draw_snake(
    screen:    pygame.Surface,
    snake:     list[tuple[int, int]],
    direction: tuple[int, int],
) -> None:
    """
    Draw the snake as a uniform rectangular tube with gap-filling connectors.

    Each body segment is drawn as a padded inset rectangle so grid lines
    remain visible at corners and bends.  Connectors are drawn only between
    CONSECUTIVE segments (snake[i] and snake[i+1]) — never between segments
    that merely happen to be grid neighbours — so the snake reads as a
    continuous tube rather than a blob.

    Parameters
    ----------
    screen    : pygame surface to draw on.
    snake     : list of (col, row) tuples, head first.
    direction : current head direction (dx, dy), used to position the eyes.
    """
    PAD = max(4, CELL // 8)

    # ── Connectors between consecutive segments (drawn first, under cells) ────
    for i in range(len(snake) - 1):
        ax, ay = snake[i]
        bx, by = snake[i + 1]

        color_a = C_HEAD if i == 0     else C_BODY_A
        color_b = C_HEAD if i + 1 == 0 else C_BODY_A

        if by == ay and bx == ax + 1:       # b is right of a
            pygame.draw.rect(screen, color_a,
                pygame.Rect(ax * CELL + CELL - PAD, ay * CELL + PAD,
                            PAD, CELL - 2 * PAD))
            pygame.draw.rect(screen, color_b,
                pygame.Rect(bx * CELL, by * CELL + PAD,
                            PAD, CELL - 2 * PAD))

        elif by == ay and bx == ax - 1:     # b is left of a
            pygame.draw.rect(screen, color_a,
                pygame.Rect(ax * CELL, ay * CELL + PAD,
                            PAD, CELL - 2 * PAD))
            pygame.draw.rect(screen, color_b,
                pygame.Rect(bx * CELL + CELL - PAD, by * CELL + PAD,
                            PAD, CELL - 2 * PAD))

        elif bx == ax and by == ay + 1:     # b is below a
            pygame.draw.rect(screen, color_a,
                pygame.Rect(ax * CELL + PAD, ay * CELL + CELL - PAD,
                            CELL - 2 * PAD, PAD))
            pygame.draw.rect(screen, color_b,
                pygame.Rect(bx * CELL + PAD, by * CELL,
                            CELL - 2 * PAD, PAD))

        elif bx == ax and by == ay - 1:     # b is above a
            pygame.draw.rect(screen, color_a,
                pygame.Rect(ax * CELL + PAD, ay * CELL,
                            CELL - 2 * PAD, PAD))
            pygame.draw.rect(screen, color_b,
                pygame.Rect(bx * CELL + PAD, by * CELL + CELL - PAD,
                            CELL - 2 * PAD, PAD))

    # ── Cell rects on top ─────────────────────────────────────────────────────
    for i, (cx, cy) in enumerate(snake):
        color  = C_HEAD if i == 0 else C_BODY_A
        radius = max(4, CELL // 10) if i == 0 else 0

        pygame.draw.rect(
            screen, color,
            pygame.Rect(cx * CELL + PAD, cy * CELL + PAD,
                        CELL - 2 * PAD, CELL - 2 * PAD),
            border_radius=radius,
        )

    # ── Eyes on the head ──────────────────────────────────────────────────────
    hx, hy = snake[0]
    cx     = hx * CELL + CELL // 2
    cy     = hy * CELL + CELL // 2
    angle  = math.atan2(direction[1], direction[0])
    perp   = angle + math.pi / 2
    for sign in (+1, -1):
        ex = int(cx + math.cos(angle) * 5 + math.cos(perp) * sign * 4)
        ey = int(cy + math.sin(angle) * 5 + math.sin(perp) * sign * 4)
        pygame.draw.circle(screen, (255, 255, 255), (ex, ey), 3)
        pygame.draw.circle(screen, C_BG,
            (int(ex + math.cos(angle)), int(ey + math.sin(angle))), 1)


def draw_food(
    screen: pygame.Surface,
    food:   tuple[int, int],
) -> None:
    """
    Draw the food as a circle with a highlight spot.

    Parameters
    ----------
    screen : pygame surface to draw on.
    food   : (col, row) position of the food.
    """
    fx, fy = food
    cx = fx * CELL + CELL // 2
    cy = fy * CELL + CELL // 2
    pygame.draw.circle(screen, C_FOOD,      (cx, cy), CELL // 2 - 3)
    pygame.draw.circle(screen, C_FOOD_SPOT, (cx - 2, cy - 2), 3)