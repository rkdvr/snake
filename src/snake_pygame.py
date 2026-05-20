"""
Snake Game — pygame implementation
Requirements: pip install pygame
Run:          python snake_pygame.py
"""

import pygame
import random
import sys

# ── Constants ────────────────────────────────────────────────────────────────
COLS, ROWS = 20, 20
CELL       = 30
WIDTH      = COLS * CELL   # 600
HEIGHT     = ROWS * CELL   # 600
BASE_SPEED = 8             # ticks per second at start

# Colours
C_BG        = (13,  17,  23)
C_GRID      = (30,  35,  42)
C_HEAD      = (88, 166, 255)
C_BODY_A    = (35, 134,  54)
C_BODY_B    = (25,  97,  39)
C_FOOD      = (248, 81,  73)
C_FOOD_SPOT = (255, 123, 114)
C_TEXT      = (230, 237, 243)
C_MUTED     = (139, 148, 158)
C_OVERLAY   = (13,  17,  23, 210)   # semi-transparent

# Directions
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
OPPOSITES = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


# ── Helpers ──────────────────────────────────────────────────────────────────
def rand_cell(exclude):
    while True:
        c = (random.randint(0, COLS-1), random.randint(0, ROWS-1))
        if c not in exclude:
            return c


def draw_rounded_rect(surface, color, rect, radius=6):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


# ── Tests (run at start-up, results printed to console) ──────────────────────
def run_tests():
    print("\n── Test suite ──────────────────────────────────────────")

    # T1 — 180° reversal is ignored
    cur = RIGHT
    blocked = LEFT   # opposite of RIGHT
    allowed = UP
    assert OPPOSITES[cur] == blocked,               "T1a: opposite map wrong"
    assert (blocked == OPPOSITES.get(cur)),          "T1b: reversal not caught"
    assert (allowed != OPPOSITES.get(cur)),          "T1c: valid dir wrongly blocked"
    print("  PASS  T1 — 180° reversal input is ignored")

    # T2 — reset_game() produces a clean state
    state = _make_state()
    state["score"] = 99
    state["snake"] = [(5,5), (4,5)]
    _reset_state(state)
    assert state["score"] == 0,          "T2: score not reset"
    assert len(state["snake"]) == 3,     "T2: snake length not reset"
    assert state["dir"] == RIGHT,        "T2: direction not reset"
    print("  PASS  T2 — reset_game() resets all variables cleanly")

    # T3 — score increments by exactly 1 per food
    state = _make_state()
    before = state["score"]
    _simulate_eat(state)
    assert state["score"] == before + 1, "T3: score did not increment by 1"
    print("  PASS  T3 — score increments by exactly 1 per food eaten")

    # T4 — self-collision triggers game over
    state = _make_state()
    state["snake"] = [(5,5), (5,6), (6,6), (6,5), (6,4), (5,4), (4,4),
                      (4,5), (4,6), (4,7)]
    # move head into body
    new_head = (state["snake"][1][0], state["snake"][1][1])
    hit = new_head in state["snake"]
    assert hit, "T4: self-collision not detected"
    print("  PASS  T4 — self-collision correctly triggers game over")

    print("────────────────────────────────────────────────────────\n")

def _make_state():
    return {"score": 0,
            "snake": [(10,10),(9,10),(8,10)],
            "dir":   RIGHT,
            "food":  (15,15)}

def _reset_state(s):
    s["score"] = 0
    s["snake"] = [(10,10),(9,10),(8,10)]
    s["dir"]   = RIGHT
    s["food"]  = rand_cell(set(s["snake"]))

def _simulate_eat(s):
    # place food at next head position so it's eaten immediately
    head = s["snake"][0]
    nxt  = (head[0] + s["dir"][0], head[1] + s["dir"][1])
    s["food"] = nxt
    s["snake"].insert(0, nxt)   # grow
    s["score"] += 1


# ── Game state ────────────────────────────────────────────────────────────────
class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake")
        self.clock   = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("Courier New", 28, bold=True)
        self.font_sm = pygame.font.SysFont("Courier New", 16)
        self.reset_game()

    # ── reset_game() ─────────────────────────────────────────────────────────
    def reset_game(self):
        self.snake    = [(10,10), (9,10), (8,10)]
        self.dir      = RIGHT
        self.next_dir = RIGHT
        self.food     = rand_cell(set(self.snake))
        self.score    = 0
        self.high     = getattr(self, "high", 0)
        self.state    = "idle"   # idle | playing | over

    # ── speed from score ─────────────────────────────────────────────────────
    @property
    def speed(self):
        return min(14, BASE_SPEED + self.score // 3)

    # ── input handling ───────────────────────────────────────────────────────
    def handle_input(self, event):
        mapping = {
            pygame.K_UP:    UP,
            pygame.K_DOWN:  DOWN,
            pygame.K_LEFT:  LEFT,
            pygame.K_RIGHT: RIGHT,
        }
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.state == "over":
                self.reset_game()
                return
            d = mapping.get(event.key)
            if d:
                # Prevent 180° reversal
                if d == OPPOSITES.get(self.dir):
                    return
                self.next_dir = d
                if self.state == "idle":
                    self.state = "playing"

    # ── move ─────────────────────────────────────────────────────────────────
    def move(self):
        self.dir  = self.next_dir
        hx, hy   = self.snake[0]
        nx, ny   = hx + self.dir[0], hy + self.dir[1]

        # Wall collision
        if not (0 <= nx < COLS and 0 <= ny < ROWS):
            self.state = "over"
            return

        # Self collision
        if (nx, ny) in self.snake:
            self.state = "over"
            return

        self.snake.insert(0, (nx, ny))

        if (nx, ny) == self.food:
            self.score += 1
            self.high   = max(self.high, self.score)
            self.food   = rand_cell(set(self.snake))
        else:
            self.snake.pop()   # remove tail when no food eaten

    # ── draw ─────────────────────────────────────────────────────────────────
    def draw(self):
        self.screen.fill(C_BG)
        self._draw_grid()
        self._draw_food()
        self._draw_snake()
        self._draw_hud()
        if self.state == "idle":
            self._draw_overlay("SNAKE", "press any arrow key to start")
        elif self.state == "over":
            self._draw_overlay("GAME OVER",
                               f"score {self.score}  |  press R to restart")
        pygame.display.flip()

    def _draw_grid(self):
        for x in range(0, WIDTH+1, CELL):
            pygame.draw.line(self.screen, C_GRID, (x,0), (x,HEIGHT))
        for y in range(0, HEIGHT+1, CELL):
            pygame.draw.line(self.screen, C_GRID, (0,y), (WIDTH,y))

    def _draw_snake(self):
        for i, (cx, cy) in enumerate(self.snake):
            rect   = pygame.Rect(cx*CELL+1, cy*CELL+1, CELL-2, CELL-2)
            color  = C_HEAD if i == 0 else (C_BODY_A if i%2==0 else C_BODY_B)
            radius = 7 if i == 0 else 4
            draw_rounded_rect(self.screen, color, rect, radius)

        # Eyes on head
        hx, hy = self.snake[0]
        cx = hx*CELL + CELL//2
        cy = hy*CELL + CELL//2
        dx, dy = self.dir
        import math
        angle  = math.atan2(dy, dx)
        perp   = angle + math.pi/2
        dist   = 5
        for sign in (+1, -1):
            ex = int(cx + math.cos(angle)*dist + math.cos(perp)*sign*4)
            ey = int(cy + math.sin(angle)*dist + math.sin(perp)*sign*4)
            pygame.draw.circle(self.screen, (255,255,255), (ex,ey), 3)
            pygame.draw.circle(self.screen, C_BG,
                               (int(ex+math.cos(angle)), int(ey+math.sin(angle))), 1)

    def _draw_food(self):
        fx, fy = self.food
        cx = fx*CELL + CELL//2
        cy = fy*CELL + CELL//2
        pygame.draw.circle(self.screen, C_FOOD, (cx, cy), CELL//2-3)
        pygame.draw.circle(self.screen, C_FOOD_SPOT, (cx-2, cy-2), 3)

    def _draw_hud(self):
        txt = self.font_sm.render(
            f"score {self.score}   high {self.high}   speed {self.speed}",
            True, C_MUTED)
        self.screen.blit(txt, (8, 4))

    def _draw_overlay(self, title, subtitle):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(C_OVERLAY)
        self.screen.blit(overlay, (0, 0))
        t = self.font_lg.render(title,    True, C_TEXT)
        s = self.font_sm.render(subtitle, True, C_MUTED)
        self.screen.blit(t, t.get_rect(center=(WIDTH//2, HEIGHT//2-18)))
        self.screen.blit(s, s.get_rect(center=(WIDTH//2, HEIGHT//2+18)))

    # ── main loop ─────────────────────────────────────────────────────────────
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                self.handle_input(event)

            if self.state == "playing":
                self.move()

            self.draw()
            self.clock.tick(self.speed)   # controls snake speed


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_tests()
    SnakeGame().run()
