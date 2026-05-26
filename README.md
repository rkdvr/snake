# Snake Game

Snake is one of the most iconic video games in history, popularized in the late 1990s when Nokia pre-installed it on its mobile phones. The player controls a growing snake that moves across a grid, eating food to grow longer — but must avoid hitting the walls or its own body. Simple in concept, endlessly replayable in practice, it became one of the first games millions of people ever played.

What makes Snake a compelling programming project is how naturally it maps to core Python concepts. The snake itself is just a list of coordinates. Movement is adding a new head and removing the tail. Collision is a membership check. Every mechanic in the game is a fundamental data structure problem in disguise, making it an ideal project for learning how code and logic translate into something you can actually play.

---

## Modes

### 1. Basic (terminal)
A text-based Snake game that runs entirely in the terminal. Uses WASD keys to steer. No dependencies beyond Python.

### 2. Pygame (playable)
A fully rendered Snake game with smooth visuals and keyboard controls. Steer with the arrow keys. The game tracks score, high score, and speed — which increases as you eat more food. Fills the board completely for a SUCCESS screen.

### 3. Solver (AI)
An AI that plays Snake automatically and fills the entire grid without ever dying. It follows a precomputed Hamiltonian cycle — a path that visits every cell exactly once — as its base strategy, and takes opportunistic shortcuts toward food when it is safe to do so. When the board is completely full, it displays a SUCCESS screen. You can pause, adjust speed, and restart via keyboard.

After closing the Pygame game, the main menu offers to run the Solver on the same seed so you can compare your route against the AI on the exact same board.

---

## How the Solver Works

The solver uses three strategies that work together:

**1. The Master Route (Hamiltonian Cycle)**

Before the game starts, the solver maps out a path that visits every cell on the grid exactly once and loops back to the beginning. No matter what happens, the snake always has this route as its guaranteed plan. As long as it follows this route, it will never trap itself and will always fill the board completely.

**2. Opportunistic Shortcuts**

While following the master route, the solver constantly looks for chances to grab food sooner. If a shortcut to the food is available and safe — meaning the snake won't cut off its own path back — it takes it. If not, it stays on the master route and waits for the food to come around naturally. Once the board is near full, shortcuts are disabled and the snake follows the master route to the finish.

**3. Tail Chase (emergent)**

Because the master route keeps the snake behind its own tail at all times, the snake naturally follows its tail around the board. This is not a separate decision — it is what following the route looks like in practice, most visible after a shortcut when the snake curves back to realign with its tail.

In plain terms: **the snake has a guaranteed plan to win, looks for faster opportunities along the way, and by design is always chasing its own tail to stay safe.**

---

## Why These Strategies

The goal was 100% grid fill — a snake that never dies and always completes the board. We evaluated several approaches before landing on the current design.

**Why not purely greedy (always chase food directly)?**

A greedy solver is fast at collecting food early on, but it has no concept of the overall board state. As the snake grows longer, greedy paths increasingly partition the free space into disconnected regions, eventually boxing the snake into a corner with no escape. It works well at low fill and fails reliably at high fill.

**Why a Hamiltonian cycle as the foundation?**

A Hamiltonian cycle visits every cell exactly once before returning to the start. A snake that follows it perfectly will always fill the board — mathematically guaranteed, no exceptions. It also eliminates the self-trapping problem entirely: because the snake's body always occupies consecutive positions on the cycle, the next step is always outside the body. No runtime safety checks needed.

**Why add greedy shortcuts on top?**

Pure cycle following works but is slow — the snake visits every cell in a fixed order regardless of where food spawns. Adding opportunistic shortcuts lets the snake collect food sooner when it is safe to do so, reducing total moves without sacrificing the safety guarantee. The safety check is simple: a shortcut is only taken if the detour keeps the snake within the safe window between its head and its own tail on the cycle.

**Why disable shortcuts past 50% fill?**

At high fill, the snake is long and the safe window between head and tail is small. The risk of a shortcut disrupting the remaining path outweighs the benefit of collecting food a few steps sooner. Switching to pure cycle following at this point ensures a clean finish.

**Why not a more optimal algorithm?**

More optimal approaches — such as deep lookahead, A* on cycle positions, or reinforcement learning — exist and would reduce total move count. We chose this design because it is explainable, deterministic, and achieves the primary goal reliably on any grid size. Correctness and clarity were prioritised over speed optimisation.

---

## Disclaimer

The solver achieves **100% board fill on approximately 99.5% of random seeds**, verified across 2,000 test runs. In rare cases (roughly 1 in 200 games), a sequence of greedy shortcuts can leave the snake with no safe move available — all four adjacent cells are occupied by its own body. When this happens, the game displays a "SOLVER STOPPED" screen and can be restarted.

This is a known limitation of the single-step safety check used by the shortcut logic. The algorithm never makes an illegal move (no wall collisions, no self-collisions) — it simply stops when it has no legal option left. A deeper lookahead would reduce this further but at significantly higher computational cost.

A test (`TestSolverReliability`) is included in the test suite to verify the success rate stays at or above 99% across 1,000 seeds. If a future code change degrades the solver, this test will catch it.

## Requirements

- Python 3.13
- pygame

---

## Setup

1. Clone the repo:
   ```
   git clone https://github.com/rkdvr/snake.git>
   cd snake
   ```

2. Create and activate the environment:
   ```
   conda env create -f environment.yaml
   conda activate snake_environment
   ```

3. Run the game:
   ```
   python main.py
   ```

---

## Controls

| Mode | Key | Action |
|---|---|---|
| Pygame | Arrow keys | Steer the snake |
| Pygame | R | Restart (game over screen) |
| Pygame | S | Hand off to the solver (same seed) |
| Pygame | Q | Quit and close window |
| Solver | Space | Pause / resume |
| Solver | R | Restart |
| Solver | + / = | Speed up |
| Solver | - | Slow down |
| Solver | Q | Quit and close window |

---

## Running Tests

```
pytest tests/ -v
```

Or by file:

```
pytest tests/test_snake_basic.py
pytest tests/test_snake_pygame.py
pytest tests/test_snake_solver.py
```

The solver test suite includes a reliability test (`TestSolverReliability`) that runs 1,000 full simulations and takes about 25 seconds. To skip it during quick development:

```
pytest tests/ -k "not TestSolverReliability"
```

---

## Project Structure

```
snake/
├── src/
│   ├── constants.py          grid dimensions, cell size, direction definitions
│   ├── theme.py              shared colours and drawing functions (snake, food)
│   ├── snake_basic.py        terminal Snake game (WASD controls)
│   ├── snake_pygame.py       playable pygame Snake (arrow key controls)
│   ├── snake_solver.py       AI solver game runner and visualiser
│   └── solver_algorithm.py   Hamiltonian cycle + greedy shortcut solver logic
├── tests/
│   ├── test_snake_basic.py
│   ├── test_snake_pygame.py
│   └── test_snake_solver.py
├── main.py                   entry point and menu
├── conftest.py               pytest path configuration
├── environment.yaml
├── requirements.txt
└── README.md
```

---

## Authors

- Lois Celorico
- Erika De Vera
- Naiza Glorioso
- Reinhard Mozo