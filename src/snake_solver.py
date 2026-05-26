"""
snake_solver.py — AI solver game runner with pygame visualisation.

The solver logic lives in solver_algorithm.py.  This file is responsible
only for the game loop, rendering, and HUD — it imports Solver and uses it,
but contains no decision-making code of its own.

Controls
--------
    SPACE       pause / resume
    R           restart with same seed
    + / =       increase speed
    -           decrease speed

Run directly
------------
    python src/snake_solver.py

Run via main menu
-----------------
    python main.py  →  choose option 3

Seed behaviour
--------------
Same as snake_pygame.py: enter a string for a reproducible run, or press
Enter to generate a unique timestamp seed shown in the HUD.

When run via main.py the seed can be passed in directly (e.g. to solve the
same board that was just played in snake_pygame).  run() returns the seed
on exit so main.py can display a summary.
"""

import sys
import math
import time
import random

import pygame

from constants          import COLS, ROWS, CELL, TOTAL_CELLS, UP, DOWN, LEFT, RIGHT
from solver_algorithm import Solver, rand_cell, CYCLE

# ── Display constants ─────────────────────────────────────────────────────────
WIDTH      = COLS * CELL          # e.g. 600 px at 10×10 with CELL=60
HEIGHT     = ROWS * CELL + 50     # play area + 50 px bottom HUD
HUD_Y      = ROWS * CELL          # y-coordinate where HUD begins
DEFAULT_FPS = 20

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG        = (13,  17,  23)
C_GRID      = (28,  33,  40)
C_HEAD      = (88, 166, 255)
C_BODY_A    = (35, 134,  54)
C_BODY_B    = (25,  97,  39)
C_FOOD      = (248, 81,  73)
C_FOOD_SPOT = (255, 123, 114)
C_TEXT      = (230, 237, 243)
C_MUTED     = (139, 148, 158)
C_OVERLAY   = (13,  17,  23, 210)
C_HUD_BG    = (22,  27,  34)
C_SAFE      = (35, 134,  54,  60)   # tail-chase / hamiltonian path hint
C_PATH      = (88, 166, 255,  80)   # greedy-food path hint


# ── Game runner ───────────────────────────────────────────────────────────────

class SnakeSolverGame:
    """
    Pygame game loop for the AI solver.

    The Solver instance (solver_algorithm.py) is called once per frame.
    This class only applies the move and updates visual state.

    Parameters
    ----------
    seed : str or int or None
        Seed for the RNG.  Pass a value to skip the interactive prompt
        (used by main.py when handing over a seed from snake_pygame).
    """

    def __init__(self, seed: str | int | None = None) -> None:
        pygame.init()
        self.screen  = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Solver")
        self.clock   = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("Courier New", 22, bold=True)
        self.font_sm = pygame.font.SysFont("Courier New", 14)

        self.fps     = DEFAULT_FPS
        self.paused  = False
        self.runs: list[dict] = []

        if seed is None:
            raw  = input("Enter seed (press Enter for random): ").strip()
            seed = raw if raw else str(int(time.time()))

        self.seed = str(seed)
        print(f"  Seed: {self.seed}\n")
        self.reset(self.seed)

    # ── State ──────────────────────────────────────────────────────────────────

    def reset(self, seed: str | None = None) -> None:
        """Reset all game state.  Optionally update the seed first."""
        if seed is not None:
            self.seed = str(seed)
        random.seed(self.seed)

        self.snake:      list[tuple[int, int]] = [CYCLE[2], CYCLE[1], CYCLE[0]]
        self.dir:        tuple[int, int]       = RIGHT
        self.food:       tuple[int, int]       = rand_cell(set(self.snake))
        self.score:      int  = 0
        self.move_count: int  = 0
        self.state:      str  = "playing"
        self.strategy:   str  = "idle"
        self.path_hint:  list = []

        # Diagnostic counters (read by tests)
        self._wall_collisions: int = 0
        self._self_collisions: int = 0
        self._move_log:        list[tuple[int, int]] = []

        # Build cycle from current starting position
        self.solver = Solver()

    # ── Simulation step ────────────────────────────────────────────────────────

    def step(self) -> None:
        """
        Ask the solver for the next move, apply it, and update game state.

        The solver's four-level safety check system runs inside
        solver.next_move().  This method only executes the resulting move
        and handles collision bookkeeping and win/loss detection.
        """
        if self.state != "playing":
            return

        head      = self.snake[0]
        snake_set = set(self.snake)

        move = self.solver.next_move(self.snake, self.food)

        # Derive strategy from the move result first, then from the solver's
        # internal attribute.  This way a mocked next_move() that returns None
        # still produces strategy='trapped' without needing solver.strategy
        # to be set as a side effect.
        if move is None:
            self.strategy  = "trapped"
            self.path_hint = []
            self.state = "over"
            self._record_run()
            return

        self.strategy  = self.solver.strategy
        self.path_hint = self._compute_path_hint(head, snake_set)

        nx, ny   = head[0] + move[0], head[1] + move[1]
        new_head = (nx, ny)

        if not (0 <= nx < COLS and 0 <= ny < ROWS):
            self._wall_collisions += 1
            self.state = "over"
            self._record_run()
            return

        if new_head in snake_set:
            self._self_collisions += 1
            self.state = "over"
            self._record_run()
            return

        self.snake.insert(0, new_head)
        self.move_count += 1
        self.dir = move

        if new_head == self.food:
            self.score += 1
            self._move_log.append((self.move_count, self.score))
            if len(self.snake) < TOTAL_CELLS:
                self.food = rand_cell(set(self.snake))
        else:
            self.snake.pop()

        if len(self.snake) == TOTAL_CELLS:
            self.state = "won"
            self._record_run()

    def _compute_path_hint(
        self,
        head:      tuple[int, int],
        snake_set: set[tuple[int, int]],
    ) -> list:
        """Return the one-step direction to the next cycle cell (for the HUD overlay)."""
        from solver_algorithm import _CYCLE_MAP, CYCLE
        head_idx  = _CYCLE_MAP[head]
        next_cell = CYCLE[(head_idx + 1) % len(CYCLE)]
        return [(next_cell[0] - head[0], next_cell[1] - head[1])]

    def _record_run(self) -> None:
        self.runs.append({
            "seed":    self.seed,
            "score":   self.score,
            "moves":   self.move_count,
            "max_len": len(self.snake),
        })

    # ── Rendering ──────────────────────────────────────────────────────────────

    def draw(self) -> None:
        self.screen.fill(C_BG)
        self._draw_grid()
        self._draw_path_hint()
        self._draw_food()
        self._draw_snake()
        self._draw_hud()

        if self.state == "over":
            self._draw_overlay(
                "SOLVER STOPPED",
                "trapped / collision  |  R to restart",
            )
        elif self.state == "won":
            self._draw_overlay(
                "SUCCESS",
                f"grid filled!  {self.move_count} moves  |  R to restart",
            )
        elif self.paused:
            self._draw_overlay("PAUSED", "SPACE to resume")

        pygame.display.flip()

    def _draw_grid(self) -> None:
        for x in range(0, WIDTH + 1, CELL):
            pygame.draw.line(self.screen, C_GRID, (x, 0), (x, ROWS * CELL))
        for y in range(0, ROWS * CELL + 1, CELL):
            pygame.draw.line(self.screen, C_GRID, (0, y), (WIDTH, y))

    def _draw_path_hint(self) -> None:
        if not self.path_hint:
            return
        surf = pygame.Surface((WIDTH, ROWS * CELL), pygame.SRCALPHA)
        pos  = self.snake[0]
        col  = C_PATH if self.strategy == "cycle" else C_SAFE  # spiral/tail-chase/flood-fill all green
        for direction in self.path_hint:
            pos = (pos[0] + direction[0], pos[1] + direction[1])
            pygame.draw.rect(
                surf, col,
                (pos[0] * CELL + 4, pos[1] * CELL + 4, CELL - 8, CELL - 8),
                border_radius=4,
            )
        self.screen.blit(surf, (0, 0))

    def _draw_snake(self) -> None:
        """
        Draw the snake as a uniform rectangular tube.

        Each segment and connector uses the same padding and no border
        radius on body cells, so the snake has consistent straight
        dimensions throughout — no wavy outline from mixed rounded cells
        and flat connectors.  A single body colour avoids the strobing
        effect of alternating shades at high speed.
        """
        PAD = max(4, CELL // 8)

        # ── Connectors between consecutive segments (drawn first) ─────────────
        for i in range(len(self.snake) - 1):
            ax, ay = self.snake[i]
            bx, by = self.snake[i + 1]

            color_a = C_HEAD if i == 0 else C_BODY_A
            color_b = C_HEAD if i + 1 == 0 else C_BODY_A

            if by == ay and bx == ax + 1:       # b is right of a
                pygame.draw.rect(self.screen, color_a,
                    pygame.Rect(ax * CELL + CELL - PAD, ay * CELL + PAD,
                                PAD, CELL - 2 * PAD))
                pygame.draw.rect(self.screen, color_b,
                    pygame.Rect(bx * CELL, by * CELL + PAD,
                                PAD, CELL - 2 * PAD))

            elif by == ay and bx == ax - 1:     # b is left of a
                pygame.draw.rect(self.screen, color_a,
                    pygame.Rect(ax * CELL, ay * CELL + PAD,
                                PAD, CELL - 2 * PAD))
                pygame.draw.rect(self.screen, color_b,
                    pygame.Rect(bx * CELL + CELL - PAD, by * CELL + PAD,
                                PAD, CELL - 2 * PAD))

            elif bx == ax and by == ay + 1:     # b is below a
                pygame.draw.rect(self.screen, color_a,
                    pygame.Rect(ax * CELL + PAD, ay * CELL + CELL - PAD,
                                CELL - 2 * PAD, PAD))
                pygame.draw.rect(self.screen, color_b,
                    pygame.Rect(bx * CELL + PAD, by * CELL,
                                CELL - 2 * PAD, PAD))

            elif bx == ax and by == ay - 1:     # b is above a
                pygame.draw.rect(self.screen, color_a,
                    pygame.Rect(ax * CELL + PAD, ay * CELL,
                                CELL - 2 * PAD, PAD))
                pygame.draw.rect(self.screen, color_b,
                    pygame.Rect(bx * CELL + PAD, by * CELL + CELL - PAD,
                                CELL - 2 * PAD, PAD))

        # ── Cell rects on top — no border_radius on body ──────────────────────
        for i, (cx, cy) in enumerate(self.snake):
            if i == 0:
                color  = C_HEAD
                radius = max(4, CELL // 10)   # head keeps slight rounding
            else:
                color  = C_BODY_A
                radius = 0                    # body is a plain rectangle

            pygame.draw.rect(
                self.screen, color,
                pygame.Rect(cx * CELL + PAD, cy * CELL + PAD,
                            CELL - 2 * PAD, CELL - 2 * PAD),
                border_radius=radius,
            )

        # ── Eyes on the head ─────────────────────────────────────────────────
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
        pygame.draw.rect(self.screen, C_HUD_BG, (0, HUD_Y, WIDTH, HEIGHT - HUD_Y))

        pct  = len(self.snake) / TOTAL_CELLS * 100
        info = (
            f"score {self.score}  |  moves {self.move_count}  |  "
            f"len {len(self.snake)}/{TOTAL_CELLS} ({pct:.0f}%)  |  "
            f"fps {self.fps}  |  strategy: {self.strategy}"
        )
        self.screen.blit(
            self.font_sm.render(info, True, C_MUTED),
            (8, HUD_Y + 8),
        )
        self.screen.blit(
            self.font_sm.render(f"seed {self.seed}", True, C_GRID),
            (WIDTH - self.font_sm.size(f"seed {self.seed}")[0] - 8, HUD_Y + 8),
        )

        bar_w = int((WIDTH - 16) * len(self.snake) / TOTAL_CELLS)
        pygame.draw.rect(
            self.screen, C_GRID,   (8, HUD_Y + 32, WIDTH - 16, 6), border_radius=3,
        )
        pygame.draw.rect(
            self.screen, C_BODY_A, (8, HUD_Y + 32, bar_w,      6), border_radius=3,
        )

    def _draw_overlay(self, title: str, sub: str) -> None:
        surf = pygame.Surface((WIDTH, ROWS * CELL), pygame.SRCALPHA)
        surf.fill(C_OVERLAY)
        self.screen.blit(surf, (0, 0))
        t = self.font_lg.render(title, True, C_TEXT)
        s = self.font_sm.render(sub,   True, C_MUTED)
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, ROWS * CELL // 2 - 16)))
        self.screen.blit(s, s.get_rect(center=(WIDTH // 2, ROWS * CELL // 2 + 16)))

    # ── Main loop ──────────────────────────────────────────────────────────────

    def run(self) -> str:
        """
        Run the solver game loop until the window is closed.

        Returns
        -------
        str
            The seed used for this session.
        """
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._print_run_summary()
                    pygame.quit()
                    return self.seed

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.reset(self.seed)
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                        self.fps = min(60, self.fps + 5)
                    elif event.key == pygame.K_MINUS:
                        self.fps = max(1, self.fps - 5)

            if not self.paused and self.state == "playing":
                self.step()

            self.draw()
            self.clock.tick(self.fps)

    def _print_run_summary(self) -> None:
        print("\n── Run summary ─────────────────────────────────────────")
        for i, r in enumerate(self.runs, 1):
            print(
                f"  Run {i}: seed={r['seed']}  score={r['score']}  "
                f"moves={r['moves']}  len={r['max_len']}/{TOTAL_CELLS}"
            )
        print("────────────────────────────────────────────────────────\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SnakeSolverGame().run()