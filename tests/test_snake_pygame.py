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
import pytest

# ── Headless pygame stub ──────────────────────────────────────────────────────
# Prevent pygame from opening a display or audio device during tests.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# ── Import the module under test ──────────────────────────────────────────────
import snake_pygame as sg
from snake_pygame import SnakeGame, BASE_SPEED, MAX_SPEED
from constants    import UP, DOWN, LEFT, RIGHT, OPPOSITES, COLS, ROWS


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def game():
    """Return a freshly initialised SnakeGame (headless)."""
    return SnakeGame(seed="test")


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
# 2. reset_game / initial state
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
# 3. Input handling
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
# 4. Movement
# ─────────────────────────────────────────────────────────────────────────────

class TestMovement:
    def test_snake_moves_forward(self, game):
        game.state    = "playing"
        game.snake    = [(3, 3), (2, 3), (1, 3)]
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
        game.snake    = [(3, 3), (2, 3), (1, 3)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (0, 0)
        game.move()
        assert len(game.snake) == 3  # length unchanged

    def test_snake_grows_on_food(self, game):
        game.state    = "playing"
        game.snake    = [(3, 3), (2, 3), (1, 3)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (4, 3)  # directly ahead
        game.move()
        assert len(game.snake) == 4

    def test_score_increments_on_food(self, game):
        game.state    = "playing"
        game.snake    = [(3, 3), (2, 3), (1, 3)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (4, 3)
        game.move()
        assert game.score == 1

    def test_high_score_updated_on_food(self, game):
        game.high     = 0
        game.state    = "playing"
        game.snake    = [(3, 3), (2, 3), (1, 3)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (4, 3)
        game.move()
        assert game.high == 1

    def test_new_food_placed_after_eating(self, game):
        game.state    = "playing"
        game.snake    = [(3, 3), (2, 3), (1, 3)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (4, 3)   # directly ahead
        game.move()
        assert game.food != (4, 3)   # old food replaced
        assert game.food not in game.snake


# ─────────────────────────────────────────────────────────────────────────────
# 5. Collision detection
# ─────────────────────────────────────────────────────────────────────────────

class TestCollisions:
    def _set_playing(self, game):
        game.state = "playing"

    def test_wall_collision_top(self, game):
        self._set_playing(game)
        game.snake    = [(3, 0), (3, 1), (3, 2)]
        game.dir      = UP
        game.next_dir = UP
        game.move()
        assert game.state == "over"

    def test_wall_collision_bottom(self, game):
        self._set_playing(game)
        game.snake    = [(3, 9), (3, 8), (3, 7)]
        game.dir      = DOWN
        game.next_dir = DOWN
        game.move()
        assert game.state == "over"

    def test_wall_collision_left(self, game):
        self._set_playing(game)
        game.snake    = [(0, 3), (1, 3), (2, 3)]
        game.dir      = LEFT
        game.next_dir = LEFT
        game.move()
        assert game.state == "over"

    def test_wall_collision_right(self, game):
        self._set_playing(game)
        game.snake    = [(9, 3), (8, 3), (7, 3)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.move()
        assert game.state == "over"

    def test_self_collision(self, game):
        self._set_playing(game)
        # Snake curled so next move hits its own body
        game.snake = [
            (2, 2), (2, 3), (3, 3), (3, 2), (3, 1),
            (2, 1), (1, 1), (1, 2), (1, 3),
        ]
        game.dir      = UP   # head at (2,2) moving UP → (2,1) which is in body
        game.next_dir = UP
        game.food     = (0, 0)
        game.move()
        assert game.state == "over"

    def test_no_false_collision(self, game):
        self._set_playing(game)
        game.snake    = [(3, 3), (2, 3), (1, 3)]
        game.dir      = RIGHT
        game.next_dir = RIGHT
        game.food     = (0, 0)
        game.move()
        assert game.state == "playing"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Speed scaling
# ─────────────────────────────────────────────────────────────────────────────

class TestSpeed:
    def test_base_speed_at_score_zero(self, game):
        game.score = 0
        assert game.speed == BASE_SPEED

    def test_speed_increases_with_score(self, game):
        game.score = 3
        assert game.speed > BASE_SPEED

    def test_speed_capped_at_max_speed(self, game):
        """Speed never exceeds MAX_SPEED regardless of score."""
        game.score = 9999
        assert game.speed == MAX_SPEED

    def test_speed_increments_every_3_points(self, game):
        """Speed increases by 1 for every 3 points scored."""
        game.score = 0
        s0 = game.speed
        game.score = 3
        s3 = game.speed
        assert s3 == s0 + 1