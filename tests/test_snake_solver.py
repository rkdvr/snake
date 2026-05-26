"""
test_snake_solver.py — Test suite for snake_solver.py and solver_algorithm.py.

Covers:
    Solver (solver_algorithm.py)  — next_move(), strategy attribute
    SnakeSolverGame               — state management, step(), _record_run()
    Integration                   — multi-step survival, score growth, seed
                                    reproduction

Headless pygame
---------------
The SDL environment variables below prevent pygame from opening a display
or audio device.  They must be set BEFORE pygame is imported anywhere.

Run
---
    pytest tests/test_snake_solver.py -v
"""

import os
import random
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from solver_algorithm import Solver, rand_cell, CYCLE
from snake_solver     import SnakeSolverGame
from constants        import (
    COLS, ROWS, TOTAL_CELLS,
    UP, DOWN, LEFT, RIGHT, DIRS, OPPOSITES,
)

# Default snake: head=CYCLE[2]=(2,0), matches SnakeSolverGame starting position
_DEFAULT_SNAKE = [CYCLE[2], CYCLE[1], CYCLE[0]]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def solver():
    return Solver()


@pytest.fixture
def game():
    """Headless SnakeSolverGame with a fixed seed."""
    return SnakeSolverGame(seed=42)


def _rand_food(snake):
    """Return a random food cell not on the snake (used in integration tests)."""
    occupied = set(snake)
    while True:
        c = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if c not in occupied:
            return c


# ── OPPOSITES map ─────────────────────────────────────────────────────────────

class TestOpposites:
    """OPPOSITES is defined in constants.py; verify it's correct."""

    def test_all_pairs_defined(self):
        assert OPPOSITES[UP]    == DOWN
        assert OPPOSITES[DOWN]  == UP
        assert OPPOSITES[LEFT]  == RIGHT
        assert OPPOSITES[RIGHT] == LEFT

    def test_double_negation(self):
        for d in DIRS:
            assert OPPOSITES[OPPOSITES[d]] == d

    def test_no_direction_is_own_opposite(self):
        for d in DIRS:
            assert OPPOSITES[d] != d


# ── Solver.next_move ──────────────────────────────────────────────────────────

class TestSolverNextMove:

    def test_returns_a_direction(self, solver):
        """next_move always returns a (dx,dy) tuple from DIRS."""
        move = solver.next_move(list(_DEFAULT_SNAKE), (5, 5))
        assert move in DIRS

    def test_does_not_reverse_into_body(self, solver):
        """Cycle step never goes backward into the snake's own body.
        Head at (2,0), body extends left — LEFT would re-enter the body."""
        move = solver.next_move(list(_DEFAULT_SNAKE), (5, 5))
        assert move != LEFT

    def test_strategy_set_after_call(self, solver):
        """strategy attribute is updated to 'cycle' or 'shortcut' after every call."""
        solver.next_move(list(_DEFAULT_SNAKE), (5, 5))
        assert solver.strategy in ("cycle", "shortcut")

    def test_shortcut_fires_toward_food(self, solver):
        """When food is directly adjacent and in the safe cycle window,
        the solver takes a shortcut and sets strategy='shortcut'."""
        # Head at CYCLE[2]=(2,0), food at CYCLE[3]=(3,0): one step right.
        # cycle_dist(head→food)=1 < cycle_dist(head→tail)=2 → safe window.
        # cycle_dist(food→food)=0 < cycle_dist(head→food)=1 → closer.
        # Shortcut should fire.
        snake = list(_DEFAULT_SNAKE)
        food  = CYCLE[3]   # (3,0) — next cycle cell, one step right
        move  = solver.next_move(snake, food)
        assert move == RIGHT
        assert solver.strategy == "shortcut"

    def test_cycle_followed_when_no_shortcut_possible(self, solver):
        """When no neighbouring cell qualifies as a shortcut, the solver
        follows the Hamiltonian cycle and strategy is 'cycle'."""
        # With an 80-cell snake, the window cycle_dist(head→tail) is small
        # and most neighbours are outside it → greedy disabled by 80% threshold.
        long_snake = [CYCLE[i] for i in range(80)]
        food  = CYCLE[85]
        move  = solver.next_move(long_snake, food)
        assert move in DIRS
        assert solver.strategy == "cycle"


# ── SnakeSolverGame — state ───────────────────────────────────────────────────

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
        game.snake = [(i % COLS, i // COLS) for i in range(10)]
        game.reset(seed=42)
        assert len(game.snake) == 3

    def test_reset_updates_seed(self, game):
        game.reset(seed=99)
        assert game.seed == "99"

    def test_reset_state_is_playing(self, game):
        game.state = "over"
        game.reset(seed=42)
        assert game.state == "playing"


# ── SnakeSolverGame — step() ──────────────────────────────────────────────────

class TestGameStep:

    def test_move_count_increments(self, game):
        before = game.move_count
        game.step()
        assert game.move_count == before + 1

    def test_snake_length_unchanged_without_food(self, game):
        game.food  = (9, 9)    # far corner, won't be eaten on first step
        game.snake = list(_DEFAULT_SNAKE)
        before     = len(game.snake)
        game.step()
        assert len(game.snake) == before

    def test_snake_grows_on_eating(self, game):
        game.snake = list(_DEFAULT_SNAKE)
        game.food  = CYCLE[3]   # (3,0): next cycle cell, eaten immediately
        before     = len(game.snake)
        game.step()
        assert len(game.snake) == before + 1

    def test_score_increments_on_eating(self, game):
        game.snake = list(_DEFAULT_SNAKE)
        game.food  = CYCLE[3]
        game.step()
        assert game.score == 1

    def test_move_log_updated_on_eating(self, game):
        game.snake = list(_DEFAULT_SNAKE)
        game.food  = CYCLE[3]
        game.step()
        assert len(game._move_log) == 1
        _, logged_score = game._move_log[0]
        assert logged_score == 1

    def test_step_exits_early_when_not_playing(self, game):
        """step() returns immediately when state != 'playing'."""
        game.state   = "over"
        before_count = game.move_count
        game.step()
        assert game.state      == "over"
        assert game.move_count == before_count

    def test_game_over_on_wall_collision(self, game):
        game._wall_collisions = 0
        game.snake            = [(0, 3), (1, 3), (2, 3)]
        game.solver.next_move = lambda s, f: LEFT   # LEFT from col 0 → wall
        game.step()
        assert game.state            == "over"
        assert game._wall_collisions == 1

    def test_game_over_on_self_collision(self, game):
        """Force the solver into its own body and check game-over detection."""
        game._self_collisions = 0
        game.snake            = [(2, 2), (3, 2), (4, 2)]
        game.solver.next_move = lambda s, f: RIGHT  # RIGHT → (3,2) = body
        game.step()
        assert game.state            == "over"
        assert game._self_collisions == 1

    def test_food_not_on_snake_after_step(self, game):
        game.step()
        assert game.food not in set(game.snake)


# ── _record_run ───────────────────────────────────────────────────────────────

class TestRecordRun:

    def test_record_appends_entry(self, game):
        before = len(game.runs)
        game._record_run()
        assert len(game.runs) == before + 1

    def test_record_correct_score(self, game):
        game.score = 7
        game._record_run()
        assert game.runs[-1]["score"] == 7

    def test_record_correct_move_count(self, game):
        game.move_count = 42
        game._record_run()
        assert game.runs[-1]["moves"] == 42

    def test_record_correct_seed(self, game):
        game.seed = "999"
        game._record_run()
        assert game.runs[-1]["seed"] == "999"

    def test_record_correct_snake_length(self, game):
        game.snake = [(i, 0) for i in range(5)]
        game._record_run()
        assert game.runs[-1]["max_len"] == 5


# ── Strategy labelling ────────────────────────────────────────────────────────

class TestStrategyLabel:

    def test_strategy_is_cycle_or_shortcut(self, game):
        """Normal step: strategy is 'cycle' or 'shortcut', never anything else."""
        game.step()
        assert game.strategy in ("cycle", "shortcut")

    def test_strategy_is_string(self, game):
        game.step()
        assert isinstance(game.strategy, str)

    def test_trapped_strategy_when_solver_returns_none(self, game):
        """When next_move() returns None, game sets strategy='trapped' itself —
        independent of solver.strategy so a mocked solver still works."""
        game.solver.next_move = lambda s, f: None
        game.step()
        assert game.strategy == "trapped"

    def test_strategy_mirrors_solver_after_normal_step(self, game):
        """game.strategy is copied from solver.strategy after each step."""
        game.step()
        assert game.strategy == game.solver.strategy


# ── Integration ───────────────────────────────────────────────────────────────

class TestIntegration:

    def test_solver_survives_200_steps(self):
        """200 steps on a 10×10 board — no wall or self collisions."""
        game = SnakeSolverGame(seed=0)
        for _ in range(200):
            if game.state != "playing":
                break
            game.step()
        assert game._wall_collisions == 0
        assert game._self_collisions == 0

    def test_score_increases_over_time(self):
        """Solver eats at least one food item in 200 steps."""
        game = SnakeSolverGame(seed=7)
        for _ in range(200):
            if game.state != "playing":
                break
            game.step()
        assert game.score > 0, "Solver never ate food in 200 steps"

    def test_move_log_is_ordered(self):
        """Move count and score both increase monotonically in the move log."""
        game = SnakeSolverGame(seed=42)
        for _ in range(200):
            if game.state != "playing":
                break
            game.step()
        log = game._move_log
        for i in range(1, len(log)):
            assert log[i][0] > log[i-1][0],      "Move count not increasing"
            assert log[i][1] == log[i-1][1] + 1,  "Score not incrementing by 1"

    def test_food_never_on_snake_after_step(self):
        """Food position is never inside the snake body after any step."""
        game = SnakeSolverGame(seed=3)
        for _ in range(200):
            if game.state != "playing":
                break
            game.step()
            assert game.food not in set(game.snake), "Food spawned on snake body"


# ── Seed reproduction ─────────────────────────────────────────────────────────

class TestSeedReproduction:

    def test_same_seed_produces_same_initial_food(self):
        """Two games with identical seeds start with the same food position."""
        a = SnakeSolverGame(seed="erika")
        b = SnakeSolverGame(seed="erika")
        assert a.food == b.food

    def test_different_seeds_produce_different_food(self):
        """Different seeds produce different initial food positions."""
        a = SnakeSolverGame(seed="erika")
        b = SnakeSolverGame(seed="lois")
        assert a.food != b.food

    def test_seed_reproduces_full_run(self):
        """Same seed produces identical score after 200 steps."""
        def run(seed):
            g = SnakeSolverGame(seed=seed)
            for _ in range(200):
                if g.state != "playing":
                    break
                g.step()
            return g.score

        assert run("erika") == run("erika")

    def test_seed_stored_as_string(self, game):
        """Seed is always stored as a string for consistent HUD display."""
        assert isinstance(game.seed, str)