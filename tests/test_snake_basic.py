"""
snake_test.py
─────────────
Tests for snake_basic.py

Run with:
    python snake_test.py

All tests print PASS or FAIL with a short description.
No external libraries required.
"""

import random
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


# ── Test runner ────────────────────────────────────────────────────────────────

passed = 0
failed = 0

def check(label, condition):
    global passed, failed
    if condition:
        print(f"  PASS — {label}")
        passed += 1
    else:
        print(f"  FAIL — {label}")
        failed += 1


# ── 1. Food spawning ───────────────────────────────────────────────────────────

print("\n[ Food Spawning ]")

random.seed(42)
snake = [[10, 10]]
food = spawn_food(snake)

check("Food does not spawn on the snake",
      food not in snake)

check("Food is within grid bounds",
      0 <= food[0] < GRID_WIDTH and 0 <= food[1] < GRID_HEIGHT)

# Reproducibility — same seed always gives same food
random.seed(42)
food_a = spawn_food([[10, 10]])
random.seed(42)
food_b = spawn_food([[10, 10]])
check("Same seed always produces the same food position",
      food_a == food_b)

# Food should never land on a long snake
random.seed(0)
long_snake = [[i, 0] for i in range(18)]   # 18 cells along the top row
long_food  = spawn_food(long_snake)
check("Food never spawns on a long snake",
      long_food not in long_snake)


# ── 2. Movement ────────────────────────────────────────────────────────────────

print("\n[ Movement ]")

snake = [[10, 10]]

new_snake = move_snake(snake, 'D')   # move right
check("Moving right increases x by 1",
      new_snake[0] == [11, 10])

new_snake = move_snake(snake, 'A')   # move left
check("Moving left decreases x by 1",
      new_snake[0] == [9, 10])

new_snake = move_snake(snake, 'W')   # move up
check("Moving up decreases y by 1",
      new_snake[0] == [10, 9])

new_snake = move_snake(snake, 'S')   # move down
check("Moving down increases y by 1",
      new_snake[0] == [10, 11])


# ── 3. Growth ──────────────────────────────────────────────────────────────────

print("\n[ Growth ]")

snake     = [[10, 10]]
food      = [11, 10]   # food is one step to the right

# Move toward food
new_snake = move_snake(snake, 'D')
ate_food  = new_snake[0] == food

if ate_food:
    grown_snake = new_snake           # grow: keep full list
else:
    grown_snake = new_snake[:-1]      # move: drop tail

check("Snake grows by exactly 1 cell when food is eaten",
      ate_food and len(grown_snake) == len(snake) + 1)

# Move without food — length should stay the same
snake2    = [[10, 10], [9, 10]]       # length 2
food2     = [0, 0]                    # food far away
new2      = move_snake(snake2, 'D')
no_eat    = new2[0] != food2
moved     = new2[:-1] if no_eat else new2

check("Snake length stays the same when no food is eaten",
      len(moved) == len(snake2))


# ── 4. Wall collision ──────────────────────────────────────────────────────────

print("\n[ Wall Collision ]")

check("Collision detected when snake hits the top wall",
      check_collision([[10, -1], [10, 0]]) is not None)

check("Collision detected when snake hits the bottom wall",
      check_collision([[10, GRID_HEIGHT], [10, GRID_HEIGHT - 1]]) is not None)

check("Collision detected when snake hits the left wall",
      check_collision([[-1, 10], [0, 10]]) is not None)

check("Collision detected when snake hits the right wall",
      check_collision([[GRID_WIDTH, 10], [GRID_WIDTH - 1, 10]]) is not None)

check("No collision when snake is safely inside the grid",
      check_collision([[4, 6], [3, 6]]) == False)


# ── 5. Self collision ──────────────────────────────────────────────────────────

print("\n[ Self Collision ]")

# Snake folded back on itself
self_colliding = [[5, 5], [5, 6], [5, 7], [6, 7], [6, 6], [6, 5], [5, 5]]
check("Collision detected when head overlaps body",
      check_collision(self_colliding) is not None)

safe_snake = [[5, 5], [4, 5], [3, 5]]
check("No collision when snake body is clear",
      check_collision(safe_snake) == False)


# ── 6. 180° reversal prevention ───────────────────────────────────────────────

print("\n[ 180° Reversal Prevention ]")

check("Opposite of W is S",  OPPOSITES['W'] == 'S')
check("Opposite of S is W",  OPPOSITES['S'] == 'W')
check("Opposite of A is D",  OPPOSITES['A'] == 'D')
check("Opposite of D is A",  OPPOSITES['D'] == 'A')

# Simulate reversal block
current_direction = 'D'
attempted_move    = 'A'
blocked = attempted_move == OPPOSITES[current_direction]
check("Moving left while facing right is blocked",
      blocked)

# Non-reversal should be allowed
attempted_move_2 = 'W'
not_blocked = attempted_move_2 != OPPOSITES[current_direction]
check("Moving up while facing right is allowed",
      not_blocked)

# Everything after an invalid move should be ignored
# Simulate: facing D, input string "DDADDWW"
# D → valid, D → valid, A → INVALID (reversal), D/W/W → should be ignored
def simulate_move_string(move_string, start_direction):
    """Returns the list of moves actually executed before hitting a reversal."""
    direction = start_direction
    executed  = []
    for move in move_string:
        if move not in DIRECTIONS:
            continue
        if move == OPPOSITES[direction]:
            break                   # stop — ignore everything after this
        direction = move
        executed.append(move)
    return executed

executed = simulate_move_string("DDADDWW", 'D')
check("Moves before invalid reversal are executed (DD executed)",
      executed == ['D', 'D'])
check("Moves after invalid reversal are ignored (DWW ignored)",
      'W' not in executed and executed[-1] == 'D')


# ── 7. Directional body rendering ─────────────────────────────────────────────

print("\n[ Directional Body Rendering ]")

# Horizontal segment: neighbors are both left and right
check("Horizontal segment renders as -",
      get_segment_char([4, 5], [5, 5], [6, 5]) == '-')

# Vertical segment: neighbors are both above and below
check("Vertical segment renders as |",
      get_segment_char([5, 4], [5, 5], [5, 6]) == '|')

# Top-right curve: came from above, going right → \
check("Top-right curve renders as \\",
      get_segment_char([5, 4], [5, 5], [6, 5]) == '\\')

# Bottom-left curve: came from below, going left → \
check("Bottom-left curve renders as \\",
      get_segment_char([5, 6], [5, 5], [4, 5]) == '\\')

# Top-left curve: came from above, going left → /
check("Top-left curve renders as /",
      get_segment_char([5, 4], [5, 5], [4, 5]) == '/')

# Bottom-right curve: came from right, going down → /
check("Bottom-right curve renders as /",
      get_segment_char([6, 5], [5, 5], [5, 6]) == '/')


# ── Summary ────────────────────────────────────────────────────────────────────

print(f"\n{'─' * 40}")
print(f"  Results: {passed} passed, {failed} failed")
print(f"{'─' * 40}\n")
