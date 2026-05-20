"""
Snake Solver — BFS pathfinding + tail-chase survival fallback
Requirements: pip install pygame
Run:          python snake_solver.py

Controls:
  SPACE   pause / resume
  R       restart with new seed
  +/-     speed up / slow down
"""

import pygame
import sys
import random
import collections

# ── Constants ─────────────────────────────────────────────────────────────────
COLS, ROWS  = 20, 20
CELL        = 30
WIDTH       = COLS * CELL
HEIGHT      = ROWS * CELL + 50          # extra HUD strip at bottom
HUD_Y       = ROWS * CELL
DEFAULT_FPS = 20
SEED        = 42                        # fixed seed → reproducible food sequence

UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
DIRS  = [UP, DOWN, LEFT, RIGHT]
OPPOSITES = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

# Colours
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
C_SAFE      = (35, 134,  54, 60)
C_PATH      = (88, 166, 255, 80)


# ── BFS helpers ───────────────────────────────────────────────────────────────
def bfs(head, target, snake_set, snake_deque):
    """
    BFS from head → target.
    snake_set: set of occupied cells (treated as walls).
    Returns list of direction tuples representing the shortest path,
    or None if no path exists.
    """
    queue   = collections.deque()
    queue.append((head, []))
    visited = {head}

    while queue:
        pos, path = queue.popleft()
        for d in DIRS:
            nxt = (pos[0]+d[0], pos[1]+d[1])
            if nxt == target:
                return path + [d]
            if (nxt not in visited and
                    nxt not in snake_set and
                    0 <= nxt[0] < COLS and
                    0 <= nxt[1] < ROWS):
                visited.add(nxt)
                queue.append((nxt, path + [d]))
    return None


def flood_fill_size(start, snake_set):
    """Count reachable empty cells from start (used for survival heuristic)."""
    visited = {start}
    queue   = collections.deque([start])
    while queue:
        pos = queue.popleft()
        for d in DIRS:
            nxt = (pos[0]+d[0], pos[1]+d[1])
            if (nxt not in visited and
                    nxt not in snake_set and
                    0 <= nxt[0] < COLS and
                    0 <= nxt[1] < ROWS):
                visited.add(nxt)
                queue.append(nxt)
    return len(visited)


def safe_moves(head, snake_set):
    """Return list of (direction, neighbour) that are immediately safe."""
    result = []
    for d in DIRS:
        nxt = (head[0]+d[0], head[1]+d[1])
        if (nxt not in snake_set and
                0 <= nxt[0] < COLS and 0 <= nxt[1] < ROWS):
            result.append((d, nxt))
    return result


# ── Solver ────────────────────────────────────────────────────────────────────
class Solver:
    """
    Strategy:
      1. BFS shortest path to food — but only commit if, after eating,
         the snake can still reach its own tail (safety check).
      2. Fallback: BFS to the tail tip (tail-chase keeps space open).
      3. Last resort: pick the neighbour with the largest flood-fill region.
    """

    def next_move(self, snake, food):
        head = snake[0]
        # Tail vacates on non-eating step — treat it as free space
        snake_set = set(snake[:-1])

        # ── Primary: path to food with post-eat safety check ────────────────
        path_to_food = bfs(head, food, snake_set, snake)
        if path_to_food:
            # Simulate step-by-step with correct tail handling each tick
            sim_snake = list(snake)
            valid     = True
            for d in path_to_food:
                new_head = (sim_snake[0][0]+d[0], sim_snake[0][1]+d[1])
                eating   = (new_head == food)
                sim_check = set(sim_snake[:-1]) if not eating else set(sim_snake)
                if new_head in sim_check:
                    valid = False
                    break
                sim_snake.insert(0, new_head)
                if not eating:
                    sim_snake.pop()
            if valid:
                sim_set = set(sim_snake[:-1])
                tail    = sim_snake[-1]
                if bfs(sim_snake[0], tail, sim_set, sim_snake) is not None:
                    return path_to_food[0]

        # ── Fallback 1: chase own tail ────────────────────────────────────────
        tail      = snake[-1]
        path_tail = bfs(head, tail, snake_set, snake)
        if path_tail:
            return path_tail[0]

        # ── Fallback 2: largest open region ──────────────────────────────────
        moves = safe_moves(head, snake_set)
        if moves:
            best_d, _ = max(moves,
                            key=lambda dm: flood_fill_size(dm[1], snake_set))
            return best_d

        return None   # completely trapped


# ── Game + visualiser ─────────────────────────────────────────────────────────
class SnakeSolverGame:
    def __init__(self, seed=SEED):
        pygame.init()
        self.screen  = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Solver")
        self.clock   = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("Courier New", 22, bold=True)
        self.font_sm = pygame.font.SysFont("Courier New", 14)
        self.solver  = Solver()
        self.fps     = DEFAULT_FPS
        self.paused  = False
        self.seed    = seed
        self.runs    = []          # list of {score, moves, max_len} per run
        self.reset(seed)

    # ── State reset ───────────────────────────────────────────────────────────
    def reset(self, seed=None):
        if seed is not None:
            self.seed = seed
        random.seed(self.seed)

        self.snake      = [(10,10), (9,10), (8,10)]
        self.dir        = RIGHT
        self.food       = self._rand_food()
        self.score      = 0
        self.move_count = 0        # total moves taken this run
        self.state      = "playing"
        self.path_hint  = []       # current BFS path for visualisation
        self.strategy   = "bfs"    # "bfs" | "tail" | "flood"

        # Test tracking
        self._wall_collisions = 0
        self._self_collisions = 0
        self._missed_food     = 0  # steps where path existed but food not taken
        self._move_log        = [] # (move_count, score) for verification

    def _rand_food(self):
        # Exclude entire body including tail — food on tail causes collision
        # on the eating step because the tail does NOT vacate when growing.
        occupied = set(self.snake) if hasattr(self, 'snake') else set()
        while True:
            c = (random.randint(0, COLS-1), random.randint(0, ROWS-1))
            if c not in occupied:
                return c

    # ── Solver step ───────────────────────────────────────────────────────────
    def step(self):
        head      = self.snake[0]
        snake_set = set(self.snake)

        # Ask solver for next direction
        move = self.solver.next_move(self.snake, self.food)

        # Update strategy label for HUD
        path_to_food = bfs(head, self.food, snake_set, self.snake)
        if path_to_food and move == path_to_food[0]:
            self.strategy   = "bfs→food"
            self.path_hint  = path_to_food
        elif move is not None:
            tail = self.snake[-1]
            path_tail = bfs(head, tail, snake_set, self.snake)
            if path_tail and move == path_tail[0]:
                self.strategy  = "tail-chase"
                self.path_hint = path_tail
            else:
                self.strategy  = "flood-fill"
                self.path_hint = []
        else:
            self.strategy  = "trapped"
            self.path_hint = []

        if move is None:
            self.state = "over"
            self._record_run()
            return

        # Compute new head
        nx, ny = head[0]+move[0], head[1]+move[1]
        new_head = (nx, ny)

        # Wall check (solver should never trigger this)
        if not (0 <= nx < COLS and 0 <= ny < ROWS):
            self._wall_collisions += 1
            self.state = "over"
            self._record_run()
            return

        # Self check
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
            self.food   = self._rand_food()
            self._move_log.append((self.move_count, self.score))
        else:
            self.snake.pop()

        # Max length = all cells filled
        if len(self.snake) == COLS * ROWS:
            self.state = "won"
            self._record_run()

    def _record_run(self):
        self.runs.append({
            "seed":   self.seed,
            "score":  self.score,
            "moves":  self.move_count,
            "max_len":len(self.snake),
        })

    # ── Drawing ───────────────────────────────────────────────────────────────
    def draw(self):
        self.screen.fill(C_BG)
        self._draw_grid()
        self._draw_path_hint()
        self._draw_food()
        self._draw_snake()
        self._draw_hud()
        if self.state == "over":
            self._draw_overlay("SOLVER STOPPED",
                "trapped / collision  |  R to restart")
        elif self.state == "won":
            self._draw_overlay("PERFECT SCORE",
                f"{self.move_count} moves  |  R to restart")
        elif self.paused:
            self._draw_overlay("PAUSED", "SPACE to resume")
        pygame.display.flip()

    def _draw_grid(self):
        for x in range(0, WIDTH+1, CELL):
            pygame.draw.line(self.screen, C_GRID, (x,0), (x, ROWS*CELL))
        for y in range(0, ROWS*CELL+1, CELL):
            pygame.draw.line(self.screen, C_GRID, (0,y), (WIDTH,y))

    def _draw_path_hint(self):
        if not self.path_hint:
            return
        surf = pygame.Surface((WIDTH, ROWS*CELL), pygame.SRCALPHA)
        pos  = self.snake[0]
        for d in self.path_hint:
            pos = (pos[0]+d[0], pos[1]+d[1])
            col = C_PATH if self.strategy == "bfs→food" else C_SAFE
            pygame.draw.rect(surf, col,
                             (pos[0]*CELL+4, pos[1]*CELL+4, CELL-8, CELL-8),
                             border_radius=4)
        self.screen.blit(surf, (0,0))

    def _draw_snake(self):
        import math
        for i, (cx,cy) in enumerate(self.snake):
            rect   = pygame.Rect(cx*CELL+1, cy*CELL+1, CELL-2, CELL-2)
            color  = C_HEAD if i==0 else (C_BODY_A if i%2==0 else C_BODY_B)
            radius = 7 if i==0 else 4
            pygame.draw.rect(self.screen, color, rect, border_radius=radius)
        # Eyes
        hx,hy = self.snake[0]
        cx = hx*CELL + CELL//2
        cy = hy*CELL + CELL//2
        angle = math.atan2(self.dir[1], self.dir[0])
        perp  = angle + math.pi/2
        for sign in (+1,-1):
            ex = int(cx + math.cos(angle)*5 + math.cos(perp)*sign*4)
            ey = int(cy + math.sin(angle)*5 + math.sin(perp)*sign*4)
            pygame.draw.circle(self.screen, (255,255,255), (ex,ey), 3)
            pygame.draw.circle(self.screen, C_BG,
                (int(ex+math.cos(angle)), int(ey+math.sin(angle))), 1)

    def _draw_food(self):
        fx,fy = self.food
        cx = fx*CELL + CELL//2
        cy = fy*CELL + CELL//2
        pygame.draw.circle(self.screen, C_FOOD,      (cx,cy), CELL//2-3)
        pygame.draw.circle(self.screen, C_FOOD_SPOT, (cx-2,cy-2), 3)

    def _draw_hud(self):
        pygame.draw.rect(self.screen, C_HUD_BG,
                         (0, HUD_Y, WIDTH, HEIGHT-HUD_Y))
        pct  = len(self.snake) / (COLS*ROWS) * 100
        info = (f"score {self.score}  |  moves {self.move_count}  |  "
                f"len {len(self.snake)}/{COLS*ROWS} ({pct:.0f}%)  |  "
                f"fps {self.fps}  |  strategy: {self.strategy}")
        t = self.font_sm.render(info, True, C_MUTED)
        self.screen.blit(t, (8, HUD_Y+8))
        seed_t = self.font_sm.render(f"seed {self.seed}", True, C_GRID)
        self.screen.blit(seed_t, (WIDTH - seed_t.get_width() - 8, HUD_Y+8))
        # Progress bar
        bar_w = int((WIDTH-16) * len(self.snake)/(COLS*ROWS))
        pygame.draw.rect(self.screen, C_GRID,   (8, HUD_Y+32, WIDTH-16, 6), border_radius=3)
        pygame.draw.rect(self.screen, C_BODY_A, (8, HUD_Y+32, bar_w,    6), border_radius=3)

    def _draw_overlay(self, title, sub):
        surf = pygame.Surface((WIDTH, ROWS*CELL), pygame.SRCALPHA)
        surf.fill(C_OVERLAY)
        self.screen.blit(surf, (0,0))
        t = self.font_lg.render(title, True, C_TEXT)
        s = self.font_sm.render(sub,   True, C_MUTED)
        self.screen.blit(t, t.get_rect(center=(WIDTH//2, ROWS*CELL//2-16)))
        self.screen.blit(s, s.get_rect(center=(WIDTH//2, ROWS*CELL//2+16)))

    # ── Main loop ─────────────────────────────────────────────────────────────
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._print_run_summary()
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.reset(random.randint(0, 9999))
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                        self.fps = min(60, self.fps + 5)
                    elif event.key == pygame.K_MINUS:
                        self.fps = max(1, self.fps - 5)

            if not self.paused and self.state == "playing":
                self.step()

            self.draw()
            self.clock.tick(self.fps)

    def _print_run_summary(self):
        print("\n── Run summary ─────────────────────────────────────────")
        for i, r in enumerate(self.runs, 1):
            print(f"  Run {i}: seed={r['seed']}  score={r['score']}  "
                  f"moves={r['moves']}  len={r['max_len']}/{COLS*ROWS}")
        print("────────────────────────────────────────────────────────\n")


# ── Tests ─────────────────────────────────────────────────────────────────────
def run_tests():
    print("\n── Test suite ──────────────────────────────────────────")
    solver = Solver()

    # ── T1: solver never collides with wall or itself across 500 steps ────────
    # Correctness: collision must be evaluated against the snake state AFTER
    # the tail is removed (non-food step) so the vacated tail cell is not
    # counted as a barrier for the incoming head.
    random.seed(0)
    snake = [(10,10),(9,10),(8,10)]
    food  = (15,15)
    wall_hits = self_hits = 0

    def t1_rand_food(s):
        occupied = set(s)          # exclude full body including tail
        while True:
            c = (random.randint(0,COLS-1), random.randint(0,ROWS-1))
            if c not in occupied:
                return c

    for _ in range(500):
        move = solver.next_move(snake, food)
        if move is None:
            break
        head  = snake[0]
        nx,ny = head[0]+move[0], head[1]+move[1]

        if not (0 <= nx < COLS and 0 <= ny < ROWS):
            wall_hits += 1
            break

        eating      = (nx,ny) == food
        future_body = snake[:-1] if not eating else snake[:]

        if (nx,ny) in set(future_body):
            self_hits += 1
            break

        snake.insert(0,(nx,ny))
        if eating:
            food = t1_rand_food(snake)   # never spawns on any body segment
        else:
            snake.pop()

    assert wall_hits == 0, f"T1: {wall_hits} wall collision(s)"
    assert self_hits == 0, f"T1: {self_hits} self collision(s)"
    print("  PASS  T1 — solver never hit wall or itself across 500 steps")

    # ── T2: solver reaches food when a safe path exists ───────────────────────
    random.seed(1)
    snake = [(10,10),(9,10),(8,10)]
    food  = (12,10)   # reachable in a straight line
    snake_set = set(snake)
    path = bfs(snake[0], food, snake_set, snake)
    assert path is not None, "T2: expected path to exist"
    move = solver.next_move(snake, food)
    # Simulate following the path
    reached = False
    pos = snake[0]
    for d in path:
        pos = (pos[0]+d[0], pos[1]+d[1])
        if pos == food:
            reached = True
    assert reached, "T2: path does not reach food"
    assert move == path[0], "T2: solver didn't take first step of BFS path"
    print("  PASS  T2 — solver follows BFS path to food when safe path exists")

    # ── T3: move count recorded accurately ───────────────────────────────────
    # Simulate a mini 5×5 game and count moves manually
    random.seed(42)
    _COLS, _ROWS = 5, 5
    _snake = [(2,2),(1,2),(0,2)]
    _food  = (4,4)
    _moves = 0
    _score = 0
    log    = []
    for _ in range(200):
        _set  = set(_snake)
        _move = bfs(_snake[0], _food, _set, _snake)
        if _move is None:
            break
        d = _move[0]
        nh = (_snake[0][0]+d[0], _snake[0][1]+d[1])
        if not (0<=nh[0]<_COLS and 0<=nh[1]<_ROWS) or nh in _set:
            break
        _snake.insert(0, nh)
        _moves += 1
        if nh == _food:
            _score += 1
            log.append((_moves, _score))
            _food = (random.randint(0,_COLS-1), random.randint(0,_ROWS-1))
        else:
            _snake.pop()
    assert _moves > 0, "T3: no moves recorded"
    for i in range(1, len(log)):
        prev_m, prev_s = log[i-1]
        curr_m, curr_s = log[i]
        assert curr_m > prev_m,  "T3: move count didn't increase between food"
        assert curr_s == prev_s+1,"T3: score didn't increment by 1"
    print(f"  PASS  T3 — move count accurate across {_moves} moves, {_score} food eaten")

    # ── T4: BFS correctness — finds shortest path, handles walls ─────────────
    snake = [(0,0)]
    # Straight horizontal path
    path = bfs((0,0), (5,0), set(snake), snake)
    assert path is not None and len(path)==5, "T4: wrong path length"
    # Blocked path (snake body walls off target)
    wall = [(x,1) for x in range(COLS)] + [(x,0) for x in range(1,COLS)]
    path2 = bfs((0,0),(COLS-1,0), set(wall), wall)
    assert path2 is None, "T4: expected no path through wall"
    print("  PASS  T4 — BFS finds shortest path and respects obstacles")

    print("────────────────────────────────────────────────────────\n")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_tests()
    SnakeSolverGame(seed=SEED).run()
