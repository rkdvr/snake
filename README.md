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

**In a nutshell:** the snake plays on a simple instinct backed by a safety net. Its instinct is greedy — whenever it can spot a clear, safe path to the food, it heads straight for it. But chasing food blindly is exactly how a snake gets itself cornered, so when no safe shortcut is available, it falls back on a fixed loop that winds through every square on the board and returns to where it started. While riding that loop, the snake is really just trailing along behind its own tail, and because the tail is always moving one step ahead of where the body ends, it can keep this up forever without ever boxing itself in. As the board fills and space gets tight, it stops taking shortcuts entirely and simply rides the loop to the end, which guarantees every square gets filled. In short: grab the food fast when it's safe, follow your own tail when it isn't, and you can't lose.

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
More optimal approaches exist but each carries significant computational cost. Deep lookahead must evaluate thousands of future board states every single move — that cost grows exponentially with snake length. A* on cycle positions becomes increasingly expensive as the board fills, and requires careful heuristic design that is hard to get right without extensive tuning. Reinforcement learning needs a training pipeline, substantial compute, and hundreds of thousands of simulated games before it produces a working policy. These are well-studied techniques in AI research, but running them in real time on a standard laptop with no GPU is impractical. The Hamiltonian cycle approach achieves the primary goal reliably with none of that overhead: each decision is a bounded index lookup, and the entire algorithm runs comfortably within a single frame.

---

## Disclaimer

The solver achieves **100% board fill on approximately 99.8% of random seeds**, verified across 1,000 test runs. In rare cases (roughly 1 in 500 games), the snake reaches a position where all four adjacent cells are occupied by its own body. When this happens, the game displays a "SOLVER STOPPED" screen and can be restarted.

This is a known limitation of the heuristic safety checks used by the shortcut logic. The algorithm never makes an illegal move (no wall collisions, no self-collisions) — it simply stops when it has no legal option left. These trapped states arise from the cycle itself at around 40% fill, not from shortcut decisions, and eliminating them entirely would require full-tree lookahead at significantly higher computational cost.

A test (`TestSolverReliability`) is included in the test suite to verify the success rate stays at or above 99% across 1,000 seeds. If a future code change degrades the solver, this test will catch it.

## Requirements

- Python 3.13
- pygame

---

## Setup

1. Clone the repo:
   ```
   git clone <your-repo-url>
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
| Basic | W / A / S / D | Steer up / left / down / right |
| Basic | Multiple keys | Chain moves in one input (e.g. WWDDS) |
| Basic | Enter | Submit moves |
| Basic | M | Return to main menu |
| Basic | Q | Quit program |
| Pygame | Arrow keys | Steer the snake |
| Pygame | R | Restart (game over screen only) |
| Pygame | S | Hand off to the solver (same seed) |
| Pygame | Esc | Return to main menu |
| Pygame | Q | Quit program |
| Solver | Space | Pause / resume |
| Solver | R | Restart |
| Solver | + / = | Speed up |
| Solver | - | Slow down |
| Solver | Esc | Return to main menu |
| Solver | Q | Quit program |

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