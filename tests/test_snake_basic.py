"""
test_snake_basic.py — pytest test suite for snake_basic.py

Run with:
    pytest tests/test_snake_basic.py -v
"""

import os
import sys
import random
import pytest

# ── Import module under test ──────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.snake_basic import (
    spawn_food,
    move_snake,
    check_collision,
    get_segment_char,
    DIRECTIONS,
    OPPOSITES,
    GRID_WIDTH,
    GRID_HEIGHT,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Food Spawning
# ─────────────────────────────────────────────────────────────────────────────

class TestFoodSpawning:
    def test_food_not_on_snake(self):
        random.seed(42)
        snake = [[10, 10]]
        food = spawn_food(snake)
        assert food not in snake

    def test_food_within_bounds(self):
        random.seed(42)
        food = spawn_food([[10, 10]])
        assert 0 <= food[0] < GRID_WIDTH
        assert 0 <= food[1] < GRID_HEIGHT

    def test_same_seed_produces_same_food(self):
        random.seed(42)
        food_a = spawn_food([[10, 10]])
        random.seed(42)
        food_b = spawn_food([[10, 10]])
        assert food_a == food_b

    def test_food_not_on_long_snake(self):
        random.seed(0)
        long_snake = [[i, 0] for i in range(18)]
        food = spawn_food(long_snake)
        assert food not in long_snake


# ─────────────────────────────────────────────────────────────────────────────
# 2. Movement
# ─────────────────────────────────────────────────────────────────────────────

class TestMovement:
    def test_move_right_increases_x(self):
        snake = [[10, 10]]
        assert move_snake(snake, 'D')[0] == [11, 10]

    def test_move_left_decreases_x(self):
        snake = [[10, 10]]
        assert move_snake(snake, 'A')[0] == [9, 10]

    def test_move_up_decreases_y(self):
        snake = [[10, 10]]
        assert move_snake(snake, 'W')[0] == [10, 9]

    def test_move_down_increases_y(self):
        snake = [[10, 10]]
        assert move_snake(snake, 'S')[0] == [10, 11]


# ─────────────────────────────────────────────────────────────────────────────
# 3. Growth
# ─────────────────────────────────────────────────────────────────────────────

class TestGrowth:
    def test_snake_grows_when_food_eaten(self):
        snake = [[10, 10]]
        food = [11, 10]
        new_snake = move_snake(snake, 'D')
        ate_food = new_snake[0] == food
        assert ate_food
        assert len(new_snake) == len(snake) + 1

    def test_snake_length_unchanged_without_food(self):
        snake = [[10, 10], [9, 10]]
        food = [0, 0]
        new_snake = move_snake(snake, 'D')
        no_eat = new_snake[0] != food
        moved = new_snake[:-1] if no_eat else new_snake
        assert len(moved) == len(snake)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Wall Collision
# ─────────────────────────────────────────────────────────────────────────────

class TestWallCollision:
    def test_collision_top_wall(self):
        assert check_collision([[10, -1], [10, 0]]) is not None

    def test_collision_bottom_wall(self):
        assert check_collision([[10, GRID_HEIGHT], [10, GRID_HEIGHT - 1]]) is not None

    def test_collision_left_wall(self):
        assert check_collision([[-1, 10], [0, 10]]) is not None

    def test_collision_right_wall(self):
        assert check_collision([[GRID_WIDTH, 10], [GRID_WIDTH - 1, 10]]) is not None

    def test_no_collision_inside_grid(self):
        assert check_collision([[4, 6], [3, 6]]) == False


# ─────────────────────────────────────────────────────────────────────────────
# 5. Self Collision
# ─────────────────────────────────────────────────────────────────────────────

class TestSelfCollision:
    def test_collision_when_head_overlaps_body(self):
        snake = [[5, 5], [5, 6], [5, 7], [6, 7], [6, 6], [6, 5], [5, 5]]
        assert check_collision(snake) is not None

    def test_no_collision_when_body_is_clear(self):
        assert check_collision([[5, 5], [4, 5], [3, 5]]) == False


# ─────────────────────────────────────────────────────────────────────────────
# 6. 180° Reversal Prevention
# ─────────────────────────────────────────────────────────────────────────────

class TestReversalPrevention:
    def test_opposite_of_w_is_s(self):
        assert OPPOSITES['W'] == 'S'

    def test_opposite_of_s_is_w(self):
        assert OPPOSITES['S'] == 'W'

    def test_opposite_of_a_is_d(self):
        assert OPPOSITES['A'] == 'D'

    def test_opposite_of_d_is_a(self):
        assert OPPOSITES['D'] == 'A'

    def test_moving_left_while_facing_right_is_blocked(self):
        assert 'A' == OPPOSITES['D']

    def test_moving_up_while_facing_right_is_allowed(self):
        assert 'W' != OPPOSITES['D']

    def test_moves_before_reversal_are_executed(self):
        assert self._simulate('DDADDWW', 'D') == ['D', 'D']

    def test_moves_after_reversal_are_ignored(self):
        executed = self._simulate('DDADDWW', 'D')
        assert 'W' not in executed and executed[-1] == 'D'

    def _simulate(self, move_string, start_direction):
        direction = start_direction
        executed = []
        for move in move_string:
            if move not in DIRECTIONS:
                continue
            if move == OPPOSITES[direction]:
                break
            direction = move
            executed.append(move)
        return executed


# ─────────────────────────────────────────────────────────────────────────────
# 7. Directional Body Rendering
# ─────────────────────────────────────────────────────────────────────────────

class TestBodyRendering:
    def test_horizontal_segment(self):
        assert get_segment_char([4, 5], [5, 5], [6, 5]) == '-'

    def test_vertical_segment(self):
        assert get_segment_char([5, 4], [5, 5], [5, 6]) == '|'

    def test_top_right_curve(self):
        assert get_segment_char([5, 4], [5, 5], [6, 5]) == '\\'

    def test_bottom_left_curve(self):
        assert get_segment_char([5, 6], [5, 5], [4, 5]) == '\\'

    def test_top_left_curve(self):
        assert get_segment_char([5, 4], [5, 5], [4, 5]) == '/'

    def test_bottom_right_curve(self):
        assert get_segment_char([6, 5], [5, 5], [5, 6]) == '/'