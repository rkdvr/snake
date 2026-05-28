import sys
import os
import random

from constants import COLS, ROWS

# ── Constants ──────────────────────────────────────────────────────────────────
# Grid dimensions come from constants.py so all three games share the same grid.
GRID_WIDTH  = COLS
GRID_HEIGHT = ROWS

EMPTY = '.'
HEAD  = 'M'
TAIL  = '~'
FOOD  = '*'

DIRECTIONS = {
    'W': ( 0, -1),
    'S': ( 0,  1),
    'A': (-1,  0),
    'D': ( 1,  0),
}

OPPOSITES = {'W': 'S', 'S': 'W', 'A': 'D', 'D': 'A'}


# ── Display ────────────────────────────────────────────────────────────────────

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_segment_char(prev, curr, nxt):
    dx1 = curr[0] - prev[0]
    dy1 = curr[1] - prev[1]
    dx2 = nxt[0]  - curr[0]
    dy2 = nxt[1]  - curr[1]

    if dy1 == 0 and dy2 == 0:
        return '-'
    if dx1 == 0 and dx2 == 0:
        return '|'

    if (dy1 == 1  and dx2 == 1)  or (dx1 == -1 and dy2 == -1) or \
       (dy1 == -1 and dx2 == -1) or (dx1 == 1  and dy2 == 1):
        return '\\'

    return '/'


def draw_board(snake, food):
    lookup = {tuple(seg): i for i, seg in enumerate(snake)}

    # Top border: each cell is 2 chars wide (char + space), so width = GRID_WIDTH * 2
    cell_width = GRID_WIDTH * 2
    border_top    = '┌' + '─' * cell_width + '┐'
    border_bottom = '└' + '─' * cell_width + '┘'

    print(border_top)
    for row in range(GRID_HEIGHT):
        line = '│'
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
        line += '│'
        print(line)
    print(border_bottom)

    print(f'\nScore: {len(snake) - 1}')
    print('  W/A/S/D move   M menu   Q quit')


# ── Game logic ─────────────────────────────────────────────────────────────────

def spawn_food(snake):
    occupied = {tuple(s) for s in snake}
    while True:
        pos = [random.randint(0, GRID_WIDTH - 1),
               random.randint(0, GRID_HEIGHT - 1)]
        if tuple(pos) not in occupied:
            return pos


def move_snake(snake, direction):
    dx, dy   = DIRECTIONS[direction]
    new_head = [snake[0][0] + dx, snake[0][1] + dy]
    return [new_head] + snake[:]


def check_collision(snake):
    head = snake[0]
    if not (0 <= head[0] < GRID_WIDTH and 0 <= head[1] < GRID_HEIGHT):
        return True
    if head in snake[1:]:
        return True
    return False


# ── Move processor ─────────────────────────────────────────────────────────────

def process_moves(move_string, snake, food, direction):
    for move in move_string:
        if move not in DIRECTIONS:
            print(f"  Unknown move '{move}' — skipping.")
            continue

        if move == OPPOSITES[direction]:
            print(f"  Invalid move '{move}' — cannot reverse direction. Remaining moves ignored.")
            break

        direction = move
        new_snake = move_snake(snake, direction)

        if check_collision(new_snake):
            snake = new_snake
            return snake, food, direction, True

        if new_snake[0] == food:
            snake = new_snake
            if len(snake) == GRID_WIDTH * GRID_HEIGHT:
                clear_screen()
                draw_board(snake, food)
                return snake, food, direction, "won"
            food = spawn_food(snake)
        else:
            snake = new_snake[:-1]

        clear_screen()
        draw_board(snake, food)

    return snake, food, direction, False


# ── Entry point ────────────────────────────────────────────────────────────────

def main(suggested_seed: str | None = None) -> str:
    clear_screen()
    print("╔══════════════════╗")
    print("║   S N A K E      ║")
    print("╚══════════════════╝")
    print("  W = up   S = down   A = left   D = right")
    print("  You can enter multiple moves at once (e.g. WWDDS).\n")

    if suggested_seed:
        seed_input = input(f"Random seed (press Enter to reuse '{suggested_seed}'): ").strip()
        seed = seed_input if seed_input else suggested_seed
    else:
        seed_input = input("Random seed (press Enter for default 42): ").strip()
        seed = seed_input if seed_input else "42"
    random.seed(seed)
    print(f"  Seed set to {seed}.\n")

    autoplay = input("Autoplay string (press Enter to skip): ").upper().strip()

    snake     = [[GRID_WIDTH // 2, GRID_HEIGHT // 2]]
    food      = spawn_food(snake)
    direction = 'D'

    clear_screen()
    draw_board(snake, food)

    game_over = False

    if autoplay:
        print("\n  Autoplaying...\n")
        snake, food, direction, game_over = process_moves(autoplay, snake, food, direction)
        if game_over == "won":
            print(f'\n  ╔══════════════════════════════╗')
            print(f'  ║   S U C C E S S              ║')
            print(f'  ║   Grid filled! Score: {len(snake) - 1:<5}  ║')
            print(f'  ╚══════════════════════════════╝')
            print(f'  Seed used: {seed}')
            return seed

    while not game_over:
        moves = input('\nYour move(s): ').upper().strip()
        if not moves:
            continue
        if moves == 'Q':
            sys.exit()
        if moves == 'M':
            return seed
        snake, food, direction, game_over = process_moves(moves, snake, food, direction)

        if game_over == "won":
            print(f'\n  ╔══════════════════════════════╗')
            print(f'  ║   S U C C E S S              ║')
            print(f'  ║   Grid filled! Score: {len(snake) - 1:<5}  ║')
            print(f'  ╚══════════════════════════════╝')
            print(f'  Seed used: {seed}')
            return seed

    if game_over == "won":
        print(f'\n  ╔══════════════════════════════╗')
        print(f'  ║   S U C C E S S              ║')
        print(f'  ║   Grid filled! Score: {len(snake) - 1:<5}  ║')
        print(f'  ╚══════════════════════════════╝')
        print(f'  Seed used: {seed}')
        return seed

    print(f'\n  Game Over!  Final score: {len(snake) - 1}')
    print(f'  Seed used: {seed}')
    return seed


if __name__ == '__main__':
    main()