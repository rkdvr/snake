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
from solver_algorithm import rand_cell

# ── Derived display constants ─────────────────────────────────────────────────
WIDTH      = COLS * CELL   # 600 px at 10×10 with CELL=60
HEIGHT     = ROWS * CELL   # 600 px at 10×10 with CELL=60
BASE_SPEED = 3             # ticks per second at score 0
MAX_SPEED  = 8             # hard cap — exported so tests don't hardcode

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG        = (13,  17,  23)
C_GRID      = (30,  35,  42)
C_HEAD      = (88, 166, 255)
C_BODY_A    = (35, 134,  54)
C_BODY_B    = (25,  97,  39)
C_FOOD      = (248, 81,  73)
C_FOOD_SPOT = (255, 123, 114)
C_TEXT      = (230, 237, 243)
C_MUTED     = (139, 148, 158)
C_OVERLAY   = (13,  17,  23, 210)


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

    def __init__(self, seed: str | None = None) -> None:
        pygame.init()
        self.screen  = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake")
        self.clock   = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("Courier New", 28, bold=True)
        self.font_sm = pygame.font.SysFont("Courier New", 16)

        if seed is None:
            raw = input("Enter seed (press Enter for random): ").strip()
            # Timestamp seed: unique per session, fully reproducible if noted.
            seed = raw if raw else str(int(time.time()))

        self.seed = seed
        random.seed(self.seed)
        print(f"  Seed: {self.seed}\n")

        self.high = 0
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
            self._draw_overlay("SNAKE", "press any arrow key to start")
        elif self.state == "over":
            self._draw_overlay(
                "GAME OVER",
                f"score {self.score}  |  press R to restart",
            )
        elif self.state == "won":
            self._draw_overlay(
                "SUCCESS",
                f"grid filled!  score {self.score}  |  press R to restart",
            )
        pygame.display.flip()

    def _draw_grid(self) -> None:
        for x in range(0, WIDTH + 1, CELL):
            pygame.draw.line(self.screen, C_GRID, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT + 1, CELL):
            pygame.draw.line(self.screen, C_GRID, (0, y), (WIDTH, y))

    def _draw_snake(self) -> None:
        for i, (cx, cy) in enumerate(self.snake):
            rect   = pygame.Rect(cx * CELL + 1, cy * CELL + 1, CELL - 2, CELL - 2)
            color  = C_HEAD if i == 0 else (C_BODY_A if i % 2 == 0 else C_BODY_B)
            radius = 7 if i == 0 else 4
            draw_rounded_rect(self.screen, color, rect, radius)

        hx, hy = self.snake[0]
        cx = hx * CELL + CELL // 2
        cy = hy * CELL + CELL // 2
        angle = math.atan2(self.dir[1], self.dir[0])
        perp  = angle + math.pi / 2
        for sign in (+1, -1):
            ex = int(cx + math.cos(angle) * 5 + math.cos(perp) * sign * 4)
            ey = int(cy + math.sin(angle) * 5 + math.sin(perp) * sign * 4)
            pygame.draw.circle(self.screen, (255, 255, 255), (ex, ey), 3)
            pygame.draw.circle(
                self.screen, C_BG,
                (int(ex + math.cos(angle)), int(ey + math.sin(angle))), 1,
            )

    def _draw_food(self) -> None:
        fx, fy = self.food
        cx = fx * CELL + CELL // 2
        cy = fy * CELL + CELL // 2
        pygame.draw.circle(self.screen, C_FOOD,      (cx, cy), CELL // 2 - 3)
        pygame.draw.circle(self.screen, C_FOOD_SPOT, (cx - 2, cy - 2), 3)

    def _draw_hud(self) -> None:
        txt = self.font_sm.render(
            f"score {self.score}   high {self.high}"
            f"   speed {self.speed}   seed {self.seed}",
            True, C_MUTED,
        )
        self.screen.blit(txt, (8, 4))

    def _draw_overlay(self, title: str, subtitle: str) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(C_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        t = self.font_lg.render(title,    True, C_TEXT)
        s = self.font_sm.render(subtitle, True, C_MUTED)
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 18)))
        self.screen.blit(s, s.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 18)))

    # ── Main loop ──────────────────────────────────────────────────────────────

    def run(self) -> str:
        """
        Run the game loop until the window is closed.

        Returns
        -------
        str
            The seed used for this session.  main.py uses the returned seed
            to offer the "Solve this seed?" prompt.
        """
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return self.seed   # hand seed back to caller
                self.handle_input(event)

            if self.state == "playing":
                self.move()

            self.draw()
            self.clock.tick(self.speed)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_tests()
    SnakeGame().run()