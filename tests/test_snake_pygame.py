"""
test_snake.py — pytest test suite for snake_pygame.py

Run with:
    pip install pytest
    pytest test_snake.py -v

Note: pygame is imported but display/audio are stubbed out via environment
variables so tests run headlessly (no window required).
"""

import os
import sys
import types
import pytest

# ── Headless pygame stub ──────────────────────────────────────────────────────
# Prevent pygame from opening a display or audio device during tests.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# ── Import the module under test ──────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import snake_pygame as sg
from snake_pygame import (
    UP, DOWN, LEFT, RIGHT, OPPOSITES,
    COLS, ROWS, BASE_SPEED,
    rand_cell, SnakeGame,
    _make_state, _reset_state, _simulate_eat,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def game():
    """Return a freshly initialised SnakeGame (headless)."""
    return SnakeGame()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Direction / OPPOSITES map
# ─────────────────────────────────────────────────────────────────────────────

class TestDirections:
    def test_all_opposites_defined(self):
        assert OPPOSITES[UP]    == DOWN
        assert OPPOSITES[DOWN]  == UP
        assert OPPOSITES[LEFT]  == RIGHT
        assert OPPOSITES[RIGHT] == LEFT

    def test_no_self_opposite(self):
        for d in (UP, DOWN, LEFT, RIGHT):
            assert OPPOSITES[d] != d


# ─────────────────────────────────────────────────────────────────────────────
# 2. rand_cell
# ─────────────────────────────────────────────────────────────────────────────

class TestRandCell:
    def test_not_in_exclude(self):
        exclude = {(5, 5), (6, 6), (7, 7)}
        for _ in range(100):
            c = rand_cell(exclude)
            assert c not in exclude

    def test_within_bounds(self):
        for _ in range(100):
            x, y = rand_cell(set())
            assert 0 <= x < COLS
            assert 0 <= y < ROWS

    def test_full_board_minus_one(self):
        """rand_cell should still find the single free cell."""
        all_cells = {(x, y) for x in range(COLS) for y in range(ROWS)}
        free = (3, 3)
        exclude = all_cells - {free}
        assert rand_cell(exclude) == free


# ─────────────────────────────────────────────────────────────────────────────
# 3. reset_game / initial state
# ─────────────────────────────────────────────────────────────────────────────

class TestReset:
    def test_initial_snake_length(self, game):
        assert len(game.snake) == 3

    def test_initial_score(self, game):
        assert game.score == 0

    def test_initial_direction(self, game):
        assert game.dir == RIGHT

    def test_initial_state_idle(self, game):
        assert game.state == "idle"

    def test_food_not_on_snake(self, game):
        assert game.food not in game.snake

    def test_high_score_preserved_across_reset(self, game):
        game.score = 10
        game.high  = 10
        game.reset_game()
        assert game.high == 10  # high score survives reset

    def test_score_cleared_on_reset(self, game):
        game.score = 42
        game.reset_game()
        assert game.score == 0


# ─────────────────────────────────────────────────────────────────────────────
# 4. Input handling
# ─────────────────────────────────────────────────────────────────────────────

import pygame

class TestInputHandling:
    def _make_key_event(self, key):
        event = pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": ""})
        return event

    def test_arrow_key_starts_game(self, game):
        assert game.state == "idle"
        game.handle_input(self._make_key_event(pygame.K_RIGHT))
        assert game.state == "playing"

    def test_180_reversal_ignored(self, game):
        game.state = "playing"
        game.dir   = RIGHT
        game.handle_input(self._make_key_event(pygame.K_LEFT))
        assert game.next_dir == RIGHT  # unchanged

    def test_valid_turn_accepted(self, game):
        game.state = "playing"
        game.dir   = RIGHT
        game.handle_input(self._make_key_event(pygame.K_UP))
        assert game.next_dir == UP

    def test_r_key_restarts_after_game_over(self, game):
        game.state = "over"
        game.score = 5
        game.handle_input(self._make_key_event(pygame.K_r))
        assert game.state == "idle"
        assert game.score == 0

    def test_r_key_ignored_during_play(self, game):
        game.state = "playing"
        game.handle_input(self._make_key_event(pygame.K_r))
        assert game.state == "playing"  # no restart mid-game


# ─────────────────────────────────────────────────────────────────────────────
# 5. Movement
# ─────────────────────────────────────────────────────────────────────────────

class TestMovement:
    def test_snake_moves_forward(self, game):
        game.state    = "playing"
        game.snake    = [(10, 10), (9, 10), (8, 10)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        # Put food somewhere irrelevant
        game.food = (0, 0)
        old_head = game.snake[0]
        game.move()
        new_head = game.snake[0]
        assert new_head == (old_head[0] + 1, old_head[1])

    def test_tail_removed_when_no_food(self, game):
        game.state    = "playing"
        game.snake    = [(10, 10), (9, 10), (8, 10)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (0, 0)
        game.move()
        assert len(game.snake) == 3  # length unchanged

    def test_snake_grows_on_food(self, game):
        game.state    = "playing"
        game.snake    = [(10, 10), (9, 10), (8, 10)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (11, 10)  # directly ahead
        game.move()
        assert len(game.snake) == 4

    def test_score_increments_on_food(self, game):
        game.state    = "playing"
        game.snake    = [(10, 10), (9, 10), (8, 10)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (11, 10)
        game.move()
        assert game.score == 1

    def test_high_score_updated_on_food(self, game):
        game.high     = 0
        game.state    = "playing"
        game.snake    = [(10, 10), (9, 10), (8, 10)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (11, 10)
        game.move()
        assert game.high == 1

    def test_new_food_placed_after_eating(self, game):
        game.state    = "playing"
        game.snake    = [(10, 10), (9, 10), (8, 10)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (11, 10)
        game.move()
        assert game.food != (11, 10)  # old food replaced
        assert game.food not in game.snake


# ─────────────────────────────────────────────────────────────────────────────
# 6. Collision detection
# ─────────────────────────────────────────────────────────────────────────────

class TestCollisions:
    def _set_playing(self, game):
        game.state = "playing"

    def test_wall_collision_top(self, game):
        self._set_playing(game)
        game.snake    = [(5, 0), (5, 1), (5, 2)]
        game.dir      = UP
        game.next_dir = UP
        game.move()
        assert game.state == "over"

    def test_wall_collision_bottom(self, game):
        self._set_playing(game)
        game.snake    = [(5, ROWS-1), (5, ROWS-2), (5, ROWS-3)]
        game.dir      = DOWN
        game.next_dir = DOWN
        game.move()
        assert game.state == "over"

    def test_wall_collision_left(self, game):
        self._set_playing(game)
        game.snake    = [(0, 5), (1, 5), (2, 5)]
        game.dir      = LEFT
        game.next_dir = LEFT
        game.move()
        assert game.state == "over"

    def test_wall_collision_right(self, game):
        self._set_playing(game)
        game.snake    = [(COLS-1, 5), (COLS-2, 5), (COLS-3, 5)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.move()
        assert game.state == "over"

    def test_self_collision(self, game):
        self._set_playing(game)
        # Snake curled so next move hits its own body
        game.snake = [
            (5, 5), (5, 6), (6, 6), (6, 5), (6, 4),
            (5, 4), (4, 4), (4, 5), (4, 6),
        ]
        game.dir      = UP   # head at (5,5) moving UP → (5,4) which is in body
        game.next_dir = UP
        game.food     = (0, 0)
        game.move()
        assert game.state == "over"

    def test_no_false_collision(self, game):
        self._set_playing(game)
        game.snake    = [(10, 10), (9, 10), (8, 10)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (0, 0)
        game.move()
        assert game.state == "playing"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Speed scaling
# ─────────────────────────────────────────────────────────────────────────────

class TestSpeed:
    def test_base_speed_at_score_zero(self, game):
        game.score = 0
        assert game.speed == BASE_SPEED

    def test_speed_increases_with_score(self, game):
        game.score = 3
        assert game.speed > BASE_SPEED

    def test_speed_capped_at_14(self, game):
        game.score = 9999
        assert game.speed == 14

    def test_speed_increments_every_3_points(self, game):
        game.score = 0
        s0 = game.speed
        game.score = 3
        s3 = game.speed
        assert s3 == s0 + 1


# ─────────────────────────────────────────────────────────────────────────────
# 8. Built-in test helpers (_make_state / _reset_state / _simulate_eat)
# ─────────────────────────────────────────────────────────────────────────────

class TestStateHelpers:
    def test_make_state_defaults(self):
        s = _make_state()
        assert s["score"] == 0
        assert len(s["snake"]) == 3
        assert s["dir"] == RIGHT

    def test_reset_state_clears_score(self):
        s = _make_state()
        s["score"] = 50
        _reset_state(s)
        assert s["score"] == 0

    def test_reset_state_snake_length(self):
        s = _make_state()
        s["snake"].extend([(7,10),(6,10)])
        _reset_state(s)
        assert len(s["snake"]) == 3

    def test_simulate_eat_grows_snake(self):
        s = _make_state()
        length_before = len(s["snake"])
        _simulate_eat(s)
        assert len(s["snake"]) == length_before + 1

    def test_simulate_eat_increments_score(self):
        s = _make_state()
        _simulate_eat(s)
        assert s["score"] == 1
