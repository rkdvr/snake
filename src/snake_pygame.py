"""
snake_pygame.py — Playable Snake game with a pygame renderer.

Controls
--------
    Arrow keys    steer the snake
    R             restart (game-over screen only)

Run directly
------------
    python src/snake_pygame.py

Run via main menu
-----------------
    python main.py  →  choose option 2

Seed behaviour
--------------
Enter any string as a seed for a reproducible game.  Press Enter to
generate a unique seed from the current timestamp — the seed is shown in
the HUD so you can note it down and replay it later, or hand it to the
solver.

When run via main.py, the game returns its seed on exit so main.py can
offer to launch the solver on the same board.
"""

import sys
import math
import time
import random

import pygame

from constants          import COLS, ROWS, CELL, TOTAL_CELLS, UP, DOWN, LEFT, RIGHT, OPPOSITES
from solver_algorithm   import rand_cell
from theme              import (
    C_BG, C_HEAD, C_BODY_A, C_BODY_B, C_FOOD, C_FOOD_SPOT,
    C_TEXT, C_MUTED, C_OVERLAY, C_GRID,
    draw_snake, draw_food,
)

# ── Derived display constants ─────────────────────────────────────────────────
WIDTH      = COLS * CELL          # 600 px at 10×10 with CELL=60
HEIGHT     = ROWS * CELL + 70     # play area + 70 px bottom HUD (two rows)
HUD_Y      = ROWS * CELL          # y-coordinate where HUD bar begins
C_HUD_BG   = (22, 27, 34)  # bottom HUD background
BASE_SPEED = 3             # ticks per second at score 0
MAX_SPEED  = 8             # hard cap — exported so tests don't hardcode


# ── Drawing helper ────────────────────────────────────────────────────────────

def draw_rounded_rect(surface, color, rect, radius: int = 6) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=radius)


# ── Built-in test suite ───────────────────────────────────────────────────────

def run_tests() -> None:
    """
    Run a quick sanity-check suite using SnakeGame's public interface.

    All assertions go through the same methods the game loop uses —
    no private helpers, no internal dict state.
    """
    print("\n── snake_pygame test suite ─────────────────────────────")

    # T1 — 180° reversal is ignored
    assert OPPOSITES[RIGHT] == LEFT,  "T1a: opposite map wrong"
    assert OPPOSITES[LEFT]  == RIGHT, "T1b: opposite map wrong"
    assert UP != OPPOSITES.get(RIGHT), "T1c: valid dir wrongly blocked"
    print("  PASS  T1 — 180° reversal input is ignored")

    # T2 — reset_game() produces a clean state
    game = SnakeGame(seed="test")
    game.score = 99
    game.snake = [(5, 5), (4, 5)]
    game.reset_game()
    assert game.score == 0,      "T2: score not reset"
    assert len(game.snake) == 3, "T2: snake length not reset"
    assert game.dir == RIGHT,    "T2: direction not reset"
    print("  PASS  T2 — reset_game() resets all variables cleanly")

    # T3 — score increments by exactly 1 per food eaten
    game = SnakeGame(seed="test")
    game.state    = "playing"
    game.snake    = [(COLS//2, ROWS//2), (COLS//2-1, ROWS//2), (COLS//2-2, ROWS//2)]
    game.dir      = RIGHT
    game.next_dir = RIGHT
    game.food     = (COLS//2+1, ROWS//2)  # directly ahead of head   # CYCLE[3]=(3,0): one step ahead of head at CYCLE[2]=(2,0)
    before = game.score
    game.move()
    assert game.score == before + 1, "T3: score did not increment by 1"
    print("  PASS  T3 — score increments by exactly 1 per food eaten")

    # T4 — self-collision triggers game over
    game = SnakeGame(seed="test")
    game.state = "playing"
    game.snake = [
        (5, 5), (5, 6), (6, 6), (6, 5), (6, 4),
        (5, 4), (4, 4), (4, 5), (4, 6),
    ]
    game.dir      = UP    # (5,5) → (5,4) which is in the body
    game.next_dir = UP
    game.food     = (0, 0)
    game.move()
    assert game.state == "over", "T4: self-collision not detected"
    print("  PASS  T4 — self-collision correctly triggers game over")

    print("────────────────────────────────────────────────────────\n")


# ── Game class ────────────────────────────────────────────────────────────────

class SnakeGame:
    """
    Pygame-rendered playable Snake game.

    Parameters
    ----------
    seed : str or None
        Seed string for the random number generator.  Pass a value to skip
        the interactive prompt (used by main.py).  Pass None to prompt the
        user at startup.
    """

    def __init__(self, seed: str | None = None, suggested_seed: str | None = None) -> None:
        pygame.init()
        self.screen  = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake")
        self.clock   = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("Courier New", 28, bold=True)
        self.font_sm = pygame.font.SysFont("Courier New", 16)

        if seed is None:
            if suggested_seed:
                raw  = input(f"Enter seed (press Enter to reuse '{suggested_seed}'): ").strip()
                seed = raw if raw else suggested_seed
            else:
                raw  = input("Enter seed (press Enter for random): ").strip()
                seed = raw if raw else str(int(time.time()))

        self.seed = seed
        random.seed(self.seed)
        print(f"  Seed: {self.seed}\n")

        self.high             = 0
        self._solve_requested = False
        self.reset_game()

    # ── State ──────────────────────────────────────────────────────────────────

    def reset_game(self) -> None:
        self.snake    = [(COLS//2, ROWS//2), (COLS//2-1, ROWS//2), (COLS//2-2, ROWS//2)]
        self.dir      = RIGHT
        self.next_dir = RIGHT
        self.food     = rand_cell(set(self.snake))
        self.score    = 0
        self.state    = "idle"

    @property
    def speed(self) -> int:
        """Ticks per second; increases with score, capped at MAX_SPEED."""
        return min(MAX_SPEED, BASE_SPEED + self.score // 3)

    # ── Input ──────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        mapping = {
            pygame.K_UP:    UP,
            pygame.K_DOWN:  DOWN,
            pygame.K_LEFT:  LEFT,
            pygame.K_RIGHT: RIGHT,
        }
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_r and self.state in ("over", "won"):
            random.seed(self.seed)
            self.reset_game()
            return

        if event.key == pygame.K_s:
            self._solve_requested = True
            return

        direction = mapping.get(event.key)
        if direction:
            if direction == OPPOSITES.get(self.dir):
                return              # ignore 180° reversal
            self.next_dir = direction
            if self.state == "idle":
                self.state = "playing"

    # ── Game logic ─────────────────────────────────────────────────────────────

    def move(self) -> None:
        self.dir   = self.next_dir
        hx, hy     = self.snake[0]
        nx, ny     = hx + self.dir[0], hy + self.dir[1]

        if not (0 <= nx < COLS and 0 <= ny < ROWS):
            self.state = "over"
            return

        if (nx, ny) in self.snake:
            self.state = "over"
            return

        self.snake.insert(0, (nx, ny))

        if (nx, ny) == self.food:
            self.score += 1
            self.high   = max(self.high, self.score)
            if len(self.snake) == TOTAL_CELLS:
                self.state = "won"
                return
            self.food = rand_cell(set(self.snake))
        else:
            self.snake.pop()

    # ── Rendering ──────────────────────────────────────────────────────────────

    def draw(self) -> None:
        self.screen.fill(C_BG)
        self._draw_grid()
        self._draw_food()
        self._draw_snake()
        self._draw_hud()

        if self.state == "idle":
            self._draw_overlay("SNAKE", "arrows · S solve · R restart · Esc menu · Q quit")
        elif self.state == "over":
            self._draw_overlay(
                "GAME OVER",
                f"score {self.score} · R restart · S solve · Esc menu · Q quit",
            )
        elif self.state == "won":
            self._draw_overlay(
                "SUCCESS",
                "grid filled! · R restart · S solve · Esc menu · Q quit",
            )
        pygame.display.flip()

    def _draw_grid(self) -> None:
        for x in range(0, WIDTH + 1, CELL):
            pygame.draw.line(self.screen, C_GRID, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT + 1, CELL):
            pygame.draw.line(self.screen, C_GRID, (0, y), (WIDTH, y))

    def _draw_snake(self) -> None:
        draw_snake(self.screen, self.snake, self.dir)


    def _draw_food(self) -> None:
        draw_food(self.screen, self.food)

    def _draw_hud(self) -> None:
        pygame.draw.rect(self.screen, C_HUD_BG, (0, HUD_Y, WIDTH, HEIGHT - HUD_Y))
        # Top row — game stats
        stats = self.font_sm.render(
            f"score {self.score}   ·   best {self.high}   ·   seed {self.seed}",
            True, C_MUTED,
        )
        # Bottom row — commands
        cmds = self.font_sm.render(
            "arrows  move     S  solve     R  restart     Esc  menu     Q  quit",
            True, C_MUTED,
        )
        self.screen.blit(stats, (8, HUD_Y + 8))
        self.screen.blit(cmds,  (8, HUD_Y + 36))

    def _draw_overlay(self, title: str, subtitle: str) -> None:
        overlay = pygame.Surface((WIDTH, ROWS * CELL), pygame.SRCALPHA)
        overlay.fill(C_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        t = self.font_lg.render(title,    True, C_TEXT)
        s = self.font_sm.render(subtitle, True, C_MUTED)
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, ROWS * CELL // 2 - 18)))
        self.screen.blit(s, s.get_rect(center=(WIDTH // 2, ROWS * CELL // 2 + 18)))

    # ── Main loop ──────────────────────────────────────────────────────────────

    def run(self) -> tuple[str, bool]:
        """
        Run the game loop until the window is closed or the user exits.

        Returns
        -------
        tuple[str, bool]
            (seed, solve_requested).  seed is the session seed.
            solve_requested is True when the user pressed S, signalling
            main.py to launch the solver immediately without prompting.

        Key bindings
        ------------
        Escape exit this game and return to the main menu.
        Q      quit the program entirely.
        """
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return self.seed, False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return self.seed, False   # exit game → back to main menu
                else:
                    self.handle_input(event)

            if self._solve_requested:
                pygame.quit()
                return self.seed, True

            if self.state == "playing":
                self.move()

            self.draw()
            self.clock.tick(self.speed)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_tests()
    seed, _ = SnakeGame().run()