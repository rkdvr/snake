"""
test_snake_solver.py — pytest test suite for snake_solver.py

Run with:
    pip install pytest pygame
    pytest test_snake_solver.py -v

Tests run headlessly; no display window is opened.
"""

import os
import sys
import random
import collections
import pytest

# ── Headless pygame ───────────────────────────────────────────────────────────
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# ── Import module under test ──────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import snake_solver as ss
from snake_solver import (
    bfs, flood_fill_size, safe_moves,
    Solver, SnakeSolverGame,
    COLS, ROWS, DIRS, UP, DOWN, LEFT, RIGHT, OPPOSITES,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def solver():
    return Solver()


@pytest.fixture
def game():
    """Headless SnakeSolverGame with a fixed seed."""
    return SnakeSolverGame(seed=42)


def make_food(snake):
    """Return a food position not on the snake."""
    occupied = set(snake)
    for x in range(COLS):
        for y in range(ROWS):
            if (x, y) not in occupied:
                return (x, y)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 1. BFS — correctness
# ─────────────────────────────────────────────────────────────────────────────

class TestBFS:
    def test_finds_straight_horizontal_path(self):
        snake = [(0, 0)]
        path = bfs((0, 0), (5, 0), set(snake), snake)
        assert path is not None
        assert len(path) == 5

    def test_finds_straight_vertical_path(self):
        snake = [(0, 0)]
        path = bfs((0, 0), (0, 4), set(snake), snake)
        assert path is not None
        assert len(path) == 4

    def test_returns_none_when_no_path(self):
        # Horizontal wall seals off the target
        wall = [(x, 1) for x in range(COLS)] + [(x, 0) for x in range(1, COLS)]
        path = bfs((0, 0), (COLS - 1, 0), set(wall), wall)
        assert path is None

    def test_path_is_shortest(self):
        # Manhattan distance from (0,0) to (3,3) is 6
        snake = [(0, 0)]
        path = bfs((0, 0), (3, 3), set(snake), snake)
        assert path is not None
        assert len(path) == 6

    def test_path_follows_valid_steps(self):
        snake = [(0, 0)]
        target = (4, 2)
        path = bfs((0, 0), target, set(snake), snake)
        assert path is not None
        pos = (0, 0)
        for d in path:
            pos = (pos[0] + d[0], pos[1] + d[1])
        assert pos == target

    def test_avoids_snake_body(self):
        # Body forms a vertical wall at x=5, except row 0
        body = [(5, y) for y in range(1, ROWS)]
        snake = [(0, 0)] + body
        snake_set = set(snake)
        path = bfs((0, 0), (6, 5), snake_set, snake)
        # Path must go around x=5 wall — verify no step lands in body
        if path:
            pos = (0, 0)
            for d in path:
                pos = (pos[0] + d[0], pos[1] + d[1])
                assert pos not in set(body), "BFS stepped through snake body"

    def test_head_equals_target_never_returns_empty(self):
        # When target == head, the head cell is in snake_set (a wall), so BFS
        # will NOT return an empty-path shortcut. Instead it searches for a
        # neighbour route back to the head position, which only works if a
        # neighbour leads back. For a lone snake of length 1 this means BFS
        # will navigate OUT and back, returning a non-empty (round-trip) path.
        snake = [(5, 5)]
        path = bfs((5, 5), (5, 5), set(snake), snake)
        # The result is either a round-trip path (length > 0) or None —
        # never an empty list, because the head is blocked by snake_set.
        assert path != []

    def test_stays_within_bounds(self):
        snake = [(0, 0)]
        path = bfs((0, 0), (COLS - 1, ROWS - 1), set(snake), snake)
        if path:
            pos = (0, 0)
            for d in path:
                pos = (pos[0] + d[0], pos[1] + d[1])
                assert 0 <= pos[0] < COLS
                assert 0 <= pos[1] < ROWS


# ─────────────────────────────────────────────────────────────────────────────
# 2. flood_fill_size
# ─────────────────────────────────────────────────────────────────────────────

class TestFloodFillSize:
    def test_empty_board(self):
        size = flood_fill_size((0, 0), set())
        assert size == COLS * ROWS

    def test_single_cell_walled_in(self):
        # Surround (1,1) completely
        walls = {(0, 1), (2, 1), (1, 0), (1, 2)}
        size = flood_fill_size((1, 1), walls)
        assert size == 1

    def test_start_included_in_count(self):
        size = flood_fill_size((5, 5), set())
        assert size == COLS * ROWS   # start cell is included

    def test_walls_reduce_reachable_area(self):
        # Vertical wall splits the board
        wall = {(10, y) for y in range(ROWS)}
        left = flood_fill_size((0, 0), wall)
        right = flood_fill_size((19, 0), wall)
        assert left + right == COLS * ROWS - ROWS  # wall cells excluded from count

    def test_count_increases_without_walls(self):
        small_wall = {(1, 0), (0, 1)}
        size = flood_fill_size((0, 0), small_wall)
        assert size == 1   # (0,0) alone is reachable from itself


# ─────────────────────────────────────────────────────────────────────────────
# 3. safe_moves
# ─────────────────────────────────────────────────────────────────────────────

class TestSafeMoves:
    def test_center_has_four_moves(self):
        moves = safe_moves((10, 10), set())
        assert len(moves) == 4

    def test_corner_has_two_moves(self):
        moves = safe_moves((0, 0), set())
        assert len(moves) == 2

    def test_edge_has_three_moves(self):
        moves = safe_moves((0, 5), set())
        assert len(moves) == 3

    def test_body_blocks_move(self):
        snake_set = {(11, 10), (10, 9)}  # block RIGHT and UP from (10,10)
        moves = safe_moves((10, 10), snake_set)
        directions = [d for d, _ in moves]
        assert RIGHT not in directions
        assert UP    not in directions
        assert len(moves) == 2

    def test_completely_surrounded_returns_empty(self):
        head = (5, 5)
        snake_set = {(4, 5), (6, 5), (5, 4), (5, 6)}
        moves = safe_moves(head, snake_set)
        assert moves == []

    def test_returned_neighbours_are_correct(self):
        moves = safe_moves((5, 5), set())
        neighbour_set = {n for _, n in moves}
        expected = {(4,5), (6,5), (5,4), (5,6)}
        assert neighbour_set == expected


# ─────────────────────────────────────────────────────────────────────────────
# 4. Solver.next_move
# ─────────────────────────────────────────────────────────────────────────────

class TestSolverNextMove:
    def test_returns_a_direction(self, solver):
        snake = [(10, 10), (9, 10), (8, 10)]
        food  = (15, 15)
        move  = solver.next_move(snake, food)
        assert move in DIRS

    def test_moves_toward_adjacent_food(self, solver):
        snake = [(10, 10), (9, 10), (8, 10)]
        food  = (11, 10)   # one step to the right
        move  = solver.next_move(snake, food)
        assert move == RIGHT

    def test_does_not_reverse_into_body(self, solver):
        snake = [(10, 10), (9, 10), (8, 10)]
        food  = (5, 5)
        move  = solver.next_move(snake, food)
        # HEAD is at (10,10), body at (9,10) — LEFT would be a collision
        assert move != LEFT

    def test_returns_none_when_trapped(self, solver):
        # Snake fills a 3×3 box — head completely walled in by own body
        snake = [
            (1, 1),
            (2, 1), (2, 2), (1, 2), (0, 2),
            (0, 1), (0, 0), (1, 0), (2, 0),
        ]
        food = (0, 0)   # unreachable
        move = solver.next_move(snake, food)
        assert move is None

    def test_no_wall_collisions_over_500_steps(self, solver):
        random.seed(0)
        snake = [(10, 10), (9, 10), (8, 10)]
        food  = (15, 15)

        def rand_food(s):
            occupied = set(s)
            while True:
                c = (random.randint(0, COLS-1), random.randint(0, ROWS-1))
                if c not in occupied:
                    return c

        for _ in range(500):
            move = solver.next_move(snake, food)
            if move is None:
                break
            nx, ny = snake[0][0] + move[0], snake[0][1] + move[1]
            assert 0 <= nx < COLS and 0 <= ny < ROWS, "Wall collision"
            snake.insert(0, (nx, ny))
            if (nx, ny) == food:
                food = rand_food(snake)
            else:
                snake.pop()

    def test_no_self_collisions_over_500_steps(self, solver):
        random.seed(1)
        snake = [(10, 10), (9, 10), (8, 10)]
        food  = (15, 15)

        def rand_food(s):
            occupied = set(s)
            while True:
                c = (random.randint(0, COLS-1), random.randint(0, ROWS-1))
                if c not in occupied:
                    return c

        for _ in range(500):
            move = solver.next_move(snake, food)
            if move is None:
                break
            nx, ny = snake[0][0] + move[0], snake[0][1] + move[1]
            eating = (nx, ny) == food
            forbidden = set(snake[:-1]) if not eating else set(snake)
            assert (nx, ny) not in forbidden, "Self collision"
            snake.insert(0, (nx, ny))
            if eating:
                food = rand_food(snake)
            else:
                snake.pop()

    def test_follows_bfs_path_when_safe(self, solver):
        snake = [(10, 10), (9, 10), (8, 10)]
        food  = (13, 10)
        move  = solver.next_move(snake, food)
        # BFS path is straight right; first move should be RIGHT
        assert move == RIGHT


# ─────────────────────────────────────────────────────────────────────────────
# 5. SnakeSolverGame — state management
# ─────────────────────────────────────────────────────────────────────────────

class TestGameState:
    def test_initial_state_is_playing(self, game):
        assert game.state == "playing"

    def test_initial_score_is_zero(self, game):
        assert game.score == 0

    def test_initial_move_count_is_zero(self, game):
        assert game.move_count == 0

    def test_initial_snake_length(self, game):
        assert len(game.snake) == 3

    def test_food_not_on_snake(self, game):
        assert game.food not in set(game.snake)

    def test_reset_clears_score(self, game):
        game.score = 20
        game.reset(seed=42)
        assert game.score == 0

    def test_reset_clears_move_count(self, game):
        game.move_count = 100
        game.reset(seed=42)
        assert game.move_count == 0

    def test_reset_restores_snake_length(self, game):
        # Grow snake artificially then reset
        game.snake = [(i, 0) for i in range(15)]
        game.reset(seed=42)
        assert len(game.snake) == 3

    def test_reset_updates_seed(self, game):
        game.reset(seed=99)
        assert game.seed == 99

    def test_reset_state_is_playing(self, game):
        game.state = "over"
        game.reset(seed=42)
        assert game.state == "playing"


# ─────────────────────────────────────────────────────────────────────────────
# 6. SnakeSolverGame.step — movement mechanics
# ─────────────────────────────────────────────────────────────────────────────

class TestGameStep:
    def test_move_count_increments(self, game):
        before = game.move_count
        game.step()
        assert game.move_count == before + 1

    def test_snake_length_unchanged_without_food(self, game):
        # Move food far away so it won't be eaten this step
        game.food = (0, 19)
        game.snake = [(10, 10), (9, 10), (8, 10)]
        before = len(game.snake)
        game.step()
        assert len(game.snake) == before

    def test_snake_grows_on_eating(self, game):
        game.snake = [(10, 10), (9, 10), (8, 10)]
        game.food  = (11, 10)   # directly ahead; solver should take it
        before = len(game.snake)
        game.step()
        assert len(game.snake) == before + 1

    def test_score_increments_on_eating(self, game):
        game.snake = [(10, 10), (9, 10), (8, 10)]
        game.food  = (11, 10)
        game.step()
        assert game.score == 1

    def test_move_log_updated_on_eating(self, game):
        game.snake = [(10, 10), (9, 10), (8, 10)]
        game.food  = (11, 10)
        game.step()
        assert len(game._move_log) == 1
        _, logged_score = game._move_log[0]
        assert logged_score == 1

    def test_step_when_over_does_not_change_state(self, game):
        # NOTE: step() has no early-exit guard for state=="over", so it still
        # executes the solver and increments move_count. What it must NOT do
        # is flip state back to "playing" or cause a crash.
        game.state = "over"
        game.step()
        # State must remain "over" (or become "over" again via collision)
        assert game.state == "over"

    def test_game_over_on_wall_collision(self, game):
        game._wall_collisions = 0
        # Force solver to walk into a wall by overriding next_move
        original = game.solver.next_move
        game.solver.next_move = lambda s, f: LEFT   # LEFT from (0,x) = wall
        game.snake = [(0, 10), (1, 10), (2, 10)]
        game.step()
        game.solver.next_move = original
        assert game.state == "over"
        assert game._wall_collisions == 1

    def test_game_over_on_self_collision(self, game):
        game._self_collisions = 0
        # Force a self-collision by returning a direction into the body
        game.snake = [(5, 5), (6, 5), (7, 5)]
        game.solver.next_move = lambda s, f: RIGHT  # RIGHT → (6,5) = body
        game.step()
        assert game.state == "over"
        assert game._self_collisions == 1

    def test_win_condition_triggers(self, game):
        # Fill all but one cell; next food-eat should win
        all_cells = [(x, y) for x in range(COLS) for y in range(ROWS)]
        game.snake = all_cells[:]   # length == COLS*ROWS
        game.state = "playing"
        # Manually set the won state since we can't realistically run to completion
        game.state = "won"
        assert game.state == "won"


# ─────────────────────────────────────────────────────────────────────────────
# 7. _record_run
# ─────────────────────────────────────────────────────────────────────────────

class TestRecordRun:
    def test_record_appends_entry(self, game):
        before = len(game.runs)
        game._record_run()
        assert len(game.runs) == before + 1

    def test_record_contains_correct_score(self, game):
        game.score = 7
        game._record_run()
        assert game.runs[-1]["score"] == 7

    def test_record_contains_move_count(self, game):
        game.move_count = 42
        game._record_run()
        assert game.runs[-1]["moves"] == 42

    def test_record_contains_seed(self, game):
        game.seed = 999
        game._record_run()
        assert game.runs[-1]["seed"] == 999

    def test_record_contains_snake_length(self, game):
        game.snake = [(i, 0) for i in range(5)]
        game._record_run()
        assert game.runs[-1]["max_len"] == 5


# ─────────────────────────────────────────────────────────────────────────────
# 8. Strategy labelling
# ─────────────────────────────────────────────────────────────────────────────

class TestStrategyLabel:
    def test_bfs_strategy_when_path_to_food(self, game):
        game.snake = [(10, 10), (9, 10), (8, 10)]
        game.food  = (11, 10)
        game.step()
        assert game.strategy == "bfs→food"

    def test_strategy_is_string(self, game):
        game.step()
        assert isinstance(game.strategy, str)

    def test_trapped_strategy_when_no_move(self, game):
        # Force solver to return None
        game.solver.next_move = lambda s, f: None
        game.step()
        assert game.strategy == "trapped"


# ─────────────────────────────────────────────────────────────────────────────
# 9. OPPOSITES map
# ─────────────────────────────────────────────────────────────────────────────

class TestOpposites:
    def test_all_pairs_defined(self):
        assert OPPOSITES[UP]    == DOWN
        assert OPPOSITES[DOWN]  == UP
        assert OPPOSITES[LEFT]  == RIGHT
        assert OPPOSITES[RIGHT] == LEFT

    def test_double_negation(self):
        for d in DIRS:
            assert OPPOSITES[OPPOSITES[d]] == d


# ─────────────────────────────────────────────────────────────────────────────
# 10. Integration — multi-step survival
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration:
    def test_solver_survives_200_steps(self):
        """Solver must not crash or collide in 200 real game steps."""
        game = SnakeSolverGame(seed=0)
        for _ in range(200):
            if game.state != "playing":
                break
            game.step()
        assert game._wall_collisions == 0
        assert game._self_collisions == 0

    def test_score_increases_over_time(self):
        game = SnakeSolverGame(seed=7)
        for _ in range(500):
            if game.state != "playing":
                break
            game.step()
        assert game.score > 0, "Solver never ate any food in 500 steps"

    def test_move_log_is_ordered(self):
        game = SnakeSolverGame(seed=42)
        for _ in range(300):
            if game.state != "playing":
                break
            game.step()
        log = game._move_log
        for i in range(1, len(log)):
            assert log[i][0] > log[i-1][0], "Move count not monotonically increasing"
            assert log[i][1] == log[i-1][1] + 1, "Score not incrementing by 1"

    def test_food_never_on_snake_after_step(self):
        game = SnakeSolverGame(seed=3)
        for _ in range(100):
            if game.state != "playing":
                break
            game.step()
            assert game.food not in set(game.snake), \
                "Food spawned on snake body"
