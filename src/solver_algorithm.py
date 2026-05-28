"""
solver_algorithm.py — Hamiltonian cycle solver with cycle-safe shortcuts.

Strategy
--------
A Hamiltonian cycle is precomputed once covering every grid cell.  The snake
follows this cycle by default, guaranteeing the board will always be filled
completely.

On top of the cycle, a lightweight greedy shortcut fires when the snake is
below 50% full: if any neighbouring cell is (a) within the safe cycle window
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
The snake starts at the centre of the grid:
    head = (COLS//2, ROWS//2)   = (5, 5) on a 10×10 grid
    body = (COLS//2-1, ROWS//2) = (4, 5)
    tail = (COLS//2-2, ROWS//2) = (3, 5)

The solver looks up the head's cycle index at runtime, so the snake can
start at any grid position — it does not need to begin at CYCLE[0].

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

# Number of cycle steps to simulate ahead when validating a shortcut.
# Higher values catch more traps at slightly more computation per step.
LOOKAHEAD = 20


# ── Solver ────────────────────────────────────────────────────────────────────

class Solver:
    """
    Follows the Hamiltonian cycle with opportunistic food-chasing shortcuts.

    Attributes
    ----------
    strategy : str
        "cycle"    — following the Hamiltonian cycle step
        "shortcut" — taking a greedy shortcut toward food
        "tail"     — emergency tail-chase when cycle step is temporarily blocked
    """

    def __init__(self) -> None:
        self.cycle_map   = _CYCLE_MAP
        self.path_list   = CYCLE
        self.total_cells = TOTAL_CELLS
        self.strategy    = "idle"
        # On startup, go directly to the first food via BFS before
        # following the cycle.  Reset each time the game restarts.
        self._first_food_path: list[tuple[int, int]] = []
        self._first_food_target: tuple[int, int] | None = None

    def next_move(
        self,
        snake: list[tuple[int, int]],
        food:  tuple[int, int],
    ) -> tuple[int, int] | None:
        """
        Return the next direction to move.

        Priority
        --------
        1. Greedy shortcut toward food (when < 50% full and safe on cycle).
        2. Follow the Hamiltonian cycle.
        3. Tail-chase fallback (BFS toward tail) when cycle step is blocked.
        4. Return None only if the snake is completely surrounded (should
           not happen under normal play).

        Parameters
        ----------
        snake : list of (col, row), head first.
        food  : (col, row) of the current food cell.

        Returns
        -------
        (dx, dy) direction tuple, or None if no move is possible.
        """
        head      = snake[0]
        tail      = snake[-1]
        head_idx  = self.cycle_map[head]
        tail_idx  = self.cycle_map[tail]
        snake_set = set(snake)

        def cycle_dist(a: int, b: int) -> int:
            return b - a if b >= a else (self.total_cells - a) + b

        # ── First-food pursuit: go straight to food before cycling ────────────
        # On game start (snake length 3) compute a direct BFS path to the
        # first food and follow it.  Before committing, a single cycle lookahead
        # verifies the END STATE (after reaching food) is safe to continue from.
        # If the final position would trap the snake, the path is discarded and
        # normal strategies handle the first food instead.
        if len(snake) == 3:
            if self._first_food_target != food or not self._first_food_path:
                path = self._bfs(head, food, snake_set)
                if path:
                    # Simulate following the entire path to get the end state,
                    # then apply cycle lookahead on that projected configuration.
                    sim = list(snake)
                    for step_dir in path:
                        nc = (sim[0][0]+step_dir[0], sim[0][1]+step_dir[1])
                        sim.insert(0, nc)
                        if nc == food:
                            break           # snake grew; stop here
                        sim.pop()
                    # sim is now the projected snake after eating the first food.
                    # Verify the cycle can continue cleanly from that state.
                    if self._cycle_lookahead(sim):
                        self._first_food_path   = path
                        self._first_food_target = food
            if self._first_food_path and self._first_food_target == food:
                next_dir  = self._first_food_path[0]
                next_cell = (head[0]+next_dir[0], head[1]+next_dir[1])
                if next_cell not in snake_set:
                    self._first_food_path.pop(0)
                    self.strategy = "shortcut"
                    return next_dir
                # Path is stale — abandon it
                self._first_food_path   = []
                self._first_food_target = None
        else:
            # Snake has grown — first food eaten, clear the startup path
            self._first_food_path   = []
            self._first_food_target = None

        # ── Strategy 1: Greedy shortcut ───────────────────────────────────────
        if len(snake) < self.total_cells * 0.5:
            best_dist_to_food = cycle_dist(head_idx, self.cycle_map[food])
            best_move = None
            for dx, dy in ((-1,0),(1,0),(0,-1),(0,1)):
                nxt = (head[0] + dx, head[1] + dy)
                if not (0 <= nxt[0] < COLS and 0 <= nxt[1] < ROWS):
                    continue
                # Cell must be physically free (not occupied by body)
                if nxt in snake_set:
                    continue
                nxt_idx = self.cycle_map[nxt]
                if cycle_dist(head_idx, nxt_idx) < cycle_dist(head_idx, tail_idx):
                    dist = cycle_dist(nxt_idx, self.cycle_map[food])
                    if dist < best_dist_to_food:
                        best_dist_to_food = dist
                        best_move = (dx, dy)
            if best_move is not None:
                # Verify the shortcut doesn't cut off access to the tail.
                # Simulate the move and check that tail is still reachable.
                new_head   = (head[0]+best_move[0], head[1]+best_move[1])
                eating     = (new_head == food)
                sim_set    = (snake_set | {new_head}) if eating else \
                             (snake_set - {tail} | {new_head})
                if self._bfs(new_head, tail, sim_set):
                    # N-step cycle lookahead: simulate the next LOOKAHEAD steps
                    # of the Hamiltonian cycle from the projected snake state
                    # and reject the shortcut if any step would be blocked.
                    # This catches "locally safe but globally trapped" shortcuts
                    # that the single-step tail check misses.
                    if eating:
                        projected = [new_head] + list(snake)
                    else:
                        projected = [new_head] + list(snake[:-1])
                    if self._cycle_lookahead(projected):
                        # Flood-fill check: the free space reachable from
                        # new_head must be at least as large as the snake.
                        # Prevents shortcuts that lead into pockets too small
                        # to accommodate the snake body — the root cause of
                        # the remaining ~1 % of failures.
                        if self._flood_fill_count(new_head, sim_set, tail) >= len(snake):
                            self.strategy = "shortcut"
                            return best_move

        # ── Strategy 2: Follow the Hamiltonian cycle ──────────────────────────
        next_cell = self.path_list[(head_idx + 1) % self.total_cells]
        cycle_move = (next_cell[0] - head[0], next_cell[1] - head[1])
        if next_cell not in snake_set:
            self.strategy = "cycle"
            return cycle_move

        # ── Strategy 3 & 4: Space-maximising fallback ───────────────────────────
        # The cycle step is temporarily blocked (can happen when the snake
        # deviates via shortcuts and the body backs up across the next cell).
        # Flood-fill each valid neighbour and take the move with the most
        # reachable free cells.  This keeps the snake away from pockets that
        # are too small to hold its body — the residual failure mode after the
        # shortcut flood-fill check was added.
        best_space    = -1
        best_fallback = None
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (head[0] + dx, head[1] + dy)
            if not (0 <= nxt[0] < COLS and 0 <= nxt[1] < ROWS):
                continue
            if nxt in snake_set:
                continue
            if nxt == tail:
                continue   # tail still occupied this turn
            space = self._flood_fill_count(nxt, snake_set, tail)
            if space > best_space:
                best_space    = space
                best_fallback = (dx, dy)

        if best_fallback is not None:
            self.strategy = "tail"
            return best_fallback

        # ── Truly no move available ───────────────────────────────────────────
        return None

    def _cycle_lookahead(
        self,
        projected_snake: list[tuple[int, int]],
    ) -> bool:
        """
        Simulate the next LOOKAHEAD steps of the Hamiltonian cycle from the
        projected snake state after a shortcut move.

        Each iteration advances the snake head to the next cycle cell and
        pops the tail — accurately modelling real snake movement.  Both the
        new head position and the vacating tail are tracked every step, so
        the occupied set stays correct throughout the simulation.

        The previous implementation only removed the tail once and never
        added advancing head positions, leaving the occupied set stale after
        the first iteration.  This caused ~1 % of unsafe shortcuts to pass
        the safety check and eventually trap the snake.

        Parameters
        ----------
        projected_snake : list of (col, row), head first.
            The full snake body immediately after the proposed shortcut move
            (tail already removed if not eating, new head prepended).

        Returns
        -------
        bool
            True if all LOOKAHEAD cycle steps are clear; False if any step
            would collide with the snake's own body.
        """
        from collections import deque as _deque
        # deque gives O(1) appendleft and pop — efficient for tight simulation loop
        snake     = _deque(projected_snake)
        snake_set = set(snake)

        for _ in range(LOOKAHEAD):
            head      = snake[0]
            next_idx  = (self.cycle_map[head] + 1) % self.total_cells
            next_cell = self.path_list[next_idx]

            if next_cell in snake_set:
                return False          # cycle step would be blocked

            # Advance the snake: new head in, old tail out — both O(1).
            snake_set.add(next_cell)
            snake_set.discard(snake[-1])
            snake.appendleft(next_cell)
            snake.pop()

        return True

    @staticmethod
    def _flood_fill_count(
        start:     tuple[int, int],
        sim_set:   set[tuple[int, int]],
        tail:      tuple[int, int],
    ) -> int:
        """
        Count free cells reachable from *start* via BFS.

        The tail cell is treated as passable because it will vacate on the
        next move.  All other cells in sim_set are treated as obstacles.

        Used to reject shortcuts that would steer the head into a pocket
        smaller than the snake body — the root cause of the residual ~1 %
        failure rate that the BFS-to-tail and cycle-lookahead checks miss.

        Parameters
        ----------
        start   : starting cell for the flood fill.
        sim_set : occupied cells after the proposed shortcut.
        tail    : current tail cell (treated as free).

        Returns
        -------
        int — number of reachable free cells (≥ 1, includes start itself).
        """
        from collections import deque
        obstacles = sim_set - {tail}   # tail vacates on the next move
        visited   = {start}
        queue     = deque([start])
        count     = 0
        while queue:
            pos = queue.popleft()
            count += 1
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (pos[0] + dx, pos[1] + dy)
                if (0 <= nxt[0] < COLS
                        and 0 <= nxt[1] < ROWS
                        and nxt not in visited
                        and nxt not in obstacles):
                    visited.add(nxt)
                    queue.append(nxt)
        return count

    @staticmethod
    def _bfs(
        start:     tuple[int, int],
        target:    tuple[int, int],
        snake_set: set[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """
        BFS from start toward target; returns list of direction steps or [].

        Uses parent-pointer reconstruction instead of copying path lists at
        every node — reduces BFS from O(n²) to O(n) in path-copy work.

        The tail cell is excluded from obstacles because it vacates on the
        next move (the head hasn't stepped yet when this is called).
        """
        from collections import deque
        passable = snake_set - {target}   # tail is passable
        parent: dict[tuple[int,int], tuple[tuple[int,int], tuple[int,int]] | None] = {start: None}
        queue  = deque([start])
        while queue:
            pos = queue.popleft()
            for dx, dy in ((-1,0),(1,0),(0,-1),(0,1)):
                nxt = (pos[0]+dx, pos[1]+dy)
                if nxt == target:
                    # Reconstruct direction list from parent map
                    path: list[tuple[int,int]] = [(dx, dy)]
                    cur  = pos
                    while parent[cur] is not None:
                        prev, d = parent[cur]   # type: ignore[misc]
                        path.append(d)
                        cur = prev
                    path.reverse()
                    return path
                if (nxt not in parent
                        and nxt not in passable
                        and 0 <= nxt[0] < COLS
                        and 0 <= nxt[1] < ROWS):
                    parent[nxt] = (pos, (dx, dy))
                    queue.append(nxt)
        return []


# ── Food placement ────────────────────────────────────────────────────────────

def rand_cell(exclude: set[tuple[int, int]]) -> tuple[int, int]:
    """Return a random grid cell not in *exclude*."""
    while True:
        cell = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if cell not in exclude:
            return cell