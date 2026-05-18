import os
import random

# ── Constants ──────────────────────────────────────────────────────────────────
GRID_WIDTH  = 20
GRID_HEIGHT = 20

EMPTY = '.'
HEAD  = 'M'
TAIL  = '~'
FOOD  = '*'

# Direction map: key → (dx, dy) in screen coordinates (y increases downward)
DIRECTIONS = {
    'W': ( 0, -1),  # up
    'S': ( 0,  1),  # down
    'A': (-1,  0),  # left
    'D': ( 1,  0),  # right
}

OPPOSITES = {'W': 'S', 'S': 'W', 'A': 'D', 'D': 'A'}


# ── Display ────────────────────────────────────────────────────────────────────

def clear_screen():
    """Clear the terminal on both Windows and Mac/Linux."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_segment_char(prev, curr, nxt):
    """
    Return the directional character for a body segment based on its neighbors.
    
    Mapping:
        Horizontal (left-right)         → -
        Vertical (up-down)              → |
        Top-right / bottom-left curve   → \\
        Top-left  / bottom-right curve  → /
    """
    dx1 = curr[0] - prev[0]
    dy1 = curr[1] - prev[1]
    dx2 = nxt[0]  - curr[0]
    dy2 = nxt[1]  - curr[1]

    # Straight segments
    if dy1 == 0 and dy2 == 0:
        return '-'
    if dx1 == 0 and dx2 == 0:
        return '|'

    # '\' corners: connects {top, right} or {bottom, left}
    if (dy1 == 1  and dx2 == 1)  or (dx1 == -1 and dy2 == -1) or \
       (dy1 == -1 and dx2 == -1) or (dx1 == 1  and dy2 == 1):
        return '\\'

    # '/' corners: connects {top, left} or {bottom, right}
    return '/'


def draw_board(snake, food):
    """Rebuild and print the full grid from scratch every turn."""
    # Map each occupied position to its index in the snake list
    lookup = {tuple(seg): i for i, seg in enumerate(snake)}

    for row in range(GRID_HEIGHT):
        line = ''
        for col in range(GRID_WIDTH):
            pos = (col, row)

            if pos == tuple(snake[0]):
                char = HEAD
            elif pos == tuple(food):
                char = FOOD
            elif pos in lookup:
                i = lookup[pos]
                if i == len(snake) - 1:
                    char = TAIL
                else:
                    char = get_segment_char(snake[i - 1], snake[i], snake[i + 1])
            else:
                char = EMPTY

            line += char + ' '
        print(line)

    print(f'\nScore: {len(snake) - 1}')


# ── Game logic ─────────────────────────────────────────────────────────────────

def spawn_food(snake):
    """Spawn food only on unoccupied cells by regenerating until a valid location is found."""
    occupied = {tuple(s) for s in snake}
    while True:
        pos = [random.randint(0, GRID_WIDTH - 1),
               random.randint(0, GRID_HEIGHT - 1)]
        if tuple(pos) not in occupied:
            return pos


def move_snake(snake, direction):
    """Return a new snake with the head moved one step in the given direction."""
    dx, dy   = DIRECTIONS[direction]
    new_head = [snake[0][0] + dx, snake[0][1] + dy]
    return [new_head] + snake[:]   # tail removal handled separately in process_moves


def check_collision(snake):
    """Return True if the snake has hit a wall or its own body."""
    head = snake[0]
    # Wall collision
    if not (0 <= head[0] < GRID_WIDTH and 0 <= head[1] < GRID_HEIGHT):
        return True
    # Self collision
    if head in snake[1:]:
        return True
    return False


# ── Move processor ─────────────────────────────────────────────────────────────

def process_moves(move_string, snake, food, direction):
    """
    Process each character in move_string as one full game step.
    Returns (snake, food, direction, game_over).
    """
    for move in move_string:
        # Skip unknown characters
        if move not in DIRECTIONS:
            print(f"  Unknown move '{move}' — skipping.")
            continue

        # Prevent 180° reversal — stop processing the entire string
        if move == OPPOSITES[direction]:
            print(f"  Invalid move '{move}' — cannot reverse direction. Remaining moves ignored.")
            break

        direction = move
        new_snake = move_snake(snake, direction)

        # Check collision before committing the move
        if check_collision(new_snake):
            snake = new_snake
            return snake, food, direction, True

        # Grow if food eaten, otherwise advance normally
        if new_snake[0] == food:
            snake = new_snake           # keep full list → snake grows by 1
            food  = spawn_food(snake)
        else:
            snake = new_snake[:-1]      # drop last tail segment → same length

        clear_screen()
        draw_board(snake, food)

    return snake, food, direction, False


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    clear_screen()
    print("╔══════════════════╗")
    print("║   S N A K E      ║")
    print("╚══════════════════╝")
    print("  W = up   S = down   A = left   D = right")
    print("  You can enter multiple moves at once (e.g. WWDDS).\n")

    # Random seed for reproducibility
    seed_input = input("Random seed (press Enter for default 42): ").strip()
    seed = int(seed_input) if seed_input.isdigit() else 42
    random.seed(seed)
    print(f"  Seed set to {seed}.\n")

    # Optional autoplay string
    autoplay = input("Autoplay string (press Enter to skip): ").upper().strip()

    # Initial game state — snake starts at center, length 1, facing right
    snake     = [[GRID_WIDTH // 2, GRID_HEIGHT // 2]]
    food      = spawn_food(snake)
    direction = 'D'

    clear_screen()
    draw_board(snake, food)

    game_over = False

    # Execute autoplay string first if provided
    if autoplay:
        print("\n  Autoplaying...\n")
        snake, food, direction, game_over = process_moves(autoplay, snake, food, direction)

    # Manual play loop
    while not game_over:
        moves = input('\nYour move(s): ').upper().strip()
        if not moves:
            continue
        snake, food, direction, game_over = process_moves(moves, snake, food, direction)

    print(f'\n  Game Over!  Final score: {len(snake) - 1}')
    print(f'  Seed used: {seed}')


if __name__ == '__main__':
    main()
