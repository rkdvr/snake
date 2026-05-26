"""
constants.py — Shared constants for all game and solver modules.

This is the single source of truth for grid dimensions, pixel sizing,
and direction definitions. Every other module imports from here so that
changing the grid size or a direction tuple only ever requires editing
one file.

Importing
---------
    from constants import COLS, ROWS, CELL, TOTAL_CELLS, UP, DOWN, LEFT, RIGHT
"""

# ── Grid dimensions ───────────────────────────────────────────────────────────

COLS        = 10          # number of columns (x-axis cells)
ROWS        = 10          # number of rows    (y-axis cells)
CELL        = 60          # pixel width/height of one cell
TOTAL_CELLS = COLS * ROWS # 100 — maximum possible snake length


# ── Directions ────────────────────────────────────────────────────────────────
# Each direction is a (dx, dy) tuple where x increases right, y increases down.

UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

DIRS = [UP, DOWN, LEFT, RIGHT]

OPPOSITES = {
    UP:    DOWN,
    DOWN:  UP,
    LEFT:  RIGHT,
    RIGHT: LEFT,
}