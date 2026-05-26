"""
solver_algorithm.py — Hamiltonian cycle solver with cycle-safe shortcuts.

Strategy
--------
A Hamiltonian cycle is precomputed once covering every grid cell.  The snake
follows this cycle by default, guaranteeing the board will always be filled
completely.

On top of the cycle, a lightweight greedy shortcut fires when the snake is
below 80% full: if any neighbouring cell is (a) within the safe cycle window
between head and tail, and (b) closer to the food on the cycle, the snake
takes that shortcut instead of the cycle step.  This makes movement responsive
to food without ever risking a trap — the cycle is always the safe fallback.

Cycle layout (column-first boustrophedon)
------------------------------------------
Row 0 is swept left → right.  Then each column from COLS-1 down to 0 is
swept alternately downward and upward through rows 1 to ROWS-1.  The last
cell in column 0 is (0, 1), which is one step from (0, 0), closing the cycle.

For a 6 × 6 grid:
    Row 0:  (0,0)→(1,0)→(2,0)→(3,0)→(4,0)→(5,0)
    Col 5↓: (5,1)→(5,2)→(5,3)→(5,4)→(5,5)
    Col 4↑: (4,5)→(4,4)→(4,3)→(4,2)→(4,1)
    Col 3↓: (3,1)→(3,2)→(3,3)→(3,4)→(3,5)
    Col 2↑: (2,5)→(2,4)→(2,3)→(2,2)→(2,1)
    Col 1↓: (1,1)→(1,2)→(1,3)→(1,4)→(1,5)
    Col 0↑: (0,5)→(0,4)→(0,3)→(0,2)→(0,1) → closes back to (0,0)

This creates a clockwise sweeping motion: right across the top, then columns
snaking right-to-left, giving the snake an organised direction at all times.

Starting position
-----------------
The snake starts at cycle indices [2, 1, 0]:
    head = CYCLE[2] = (2, 0)
    body = CYCLE[1] = (1, 0)
    tail = CYCLE[0] = (0, 0)

Importing
---------
    from solver_algorithm import Solver, CYCLE, rand_cell
"""

import random
from constants import COLS, ROWS, TOTAL_CELLS


# ── Cycle construction ────────────────────────────────────────────────────────

def _build_cycle() -> tuple[list[tuple[int, int]], dict[tuple[int, int], int]]:
    """
    Build the column-first boustrophedon Hamiltonian cycle.

    Returns
    -------
    path_list : list of (col, row)
        TOTAL_CELLS cells in cycle order.
    cycle_map : dict mapping (col, row) → cycle index
        Reverse lookup for O(1) position queries.
    """
    path_list: list[tuple[int, int]] = []

    # Row 0: left to right
    for x in range(COLS):
        path_list.append((x, 0))

    # Columns COLS-1 down to 0, alternating direction
    for x in range(COLS - 1, -1, -1):
        if (COLS - 1 - x) % 2 == 0:
            for y in range(1, ROWS):          # downward
                path_list.append((x, y))
        else:
            for y in range(ROWS - 1, 0, -1):  # upward
                path_list.append((x, y))

    cycle_map: dict[tuple[int, int], int] = {
        coord: idx for idx, coord in enumerate(path_list)
    }
    return path_list, cycle_map


CYCLE, _CYCLE_MAP = _build_cycle()


# ── Solver ────────────────────────────────────────────────────────────────────

class Solver:
    """
    Follows the Hamiltonian cycle with opportunistic food-chasing shortcuts.

    Attributes
    ----------
    strategy : str
        "cycle" when following the cycle step, "shortcut" when deviating
        toward food.
    """

    def __init__(self) -> None:
        self.cycle_map  = _CYCLE_MAP
        self.path_list  = CYCLE
        self.total_cells = TOTAL_CELLS
        self.strategy   = "idle"

    def next_move(
        self,
        snake: list[tuple[int, int]],
        food:  tuple[int, int],
    ) -> tuple[int, int]:
        """
        Return the next direction to move.

        Default: follow the precomputed Hamiltonian cycle.
        Override: if the snake is below 80% full, check all four neighbours.
        If a neighbour is (1) within the safe cycle window between head and
        tail, and (2) brings us closer to the food on the cycle, take it.

        Parameters
        ----------
        snake : list of (col, row), head first.
        food  : (col, row) of the current food cell.

        Returns
        -------
        (dx, dy) direction tuple.
        """
        head      = snake[0]
        tail      = snake[-1]
        head_idx  = self.cycle_map[head]
        tail_idx  = self.cycle_map[tail]

        def cycle_dist(a: int, b: int) -> int:
            """Forward steps from cycle index a to index b."""
            return b - a if b >= a else (self.total_cells - a) + b

        # Default: next step on the Hamiltonian cycle (always safe)
        next_cell = self.path_list[(head_idx + 1) % self.total_cells]
        best_move = (next_cell[0] - head[0], next_cell[1] - head[1])
        self.strategy = "cycle"

        # Greedy shortcut: only when board is less than 80% full
        if len(snake) < self.total_cells * 0.80:
            best_dist_to_food = cycle_dist(head_idx, self.cycle_map[food])
            for dx, dy in ((-1,0),(1,0),(0,-1),(0,1)):
                nxt = (head[0] + dx, head[1] + dy)
                if not (0 <= nxt[0] < COLS and 0 <= nxt[1] < ROWS):
                    continue
                nxt_idx = self.cycle_map[nxt]
                # Safety: nxt must be within the window head → tail on cycle
                if cycle_dist(head_idx, nxt_idx) < cycle_dist(head_idx, tail_idx):
                    # Greedy: nxt must be closer to food than our current best
                    dist = cycle_dist(nxt_idx, self.cycle_map[food])
                    if dist < best_dist_to_food:
                        best_dist_to_food = dist
                        best_move = (dx, dy)
                        self.strategy = "shortcut"

        return best_move


# ── Food placement ────────────────────────────────────────────────────────────

def rand_cell(exclude: set[tuple[int, int]]) -> tuple[int, int]:
    """Return a random grid cell not in *exclude*."""
    while True:
        cell = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if cell not in exclude:
            return cell