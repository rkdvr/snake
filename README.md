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

Approaches that would push reliability to a true 100% — deep multi-step lookahead, a shortest-path search (A\*) over cycle positions, or a reinforcement-learning policy — are well-studied in AI research, but each carries a cost this project deliberately avoids: lookahead grows exponentially with snake length, A\* gets steadily more expensive as the board fills and needs careful heuristic tuning, and RL needs a training pipeline, real compute, and hundreds of thousands of simulated games before it works at all. None of that runs comfortably in real time on a standard laptop with no GPU. The Hamiltonian cycle approach hits the primary goal reliably with none of that overhead: every decision is a bounded lookup that finishes within a single frame. The residual ~0.1% failure rate and concrete, low-cost ways to reduce it further are examined in the Error Analysis section.

---

## Disclaimer

The solver fills the board completely on roughly **99.9%** of random seeds. In the rare remaining case it reaches a position where every cell next to the head is its own body or a wall; the game shows a "SOLVER STOPPED" screen and can be restarted. The solver never makes an illegal move — it only ever halts when no legal move is left.

The measured success rate, how it was tested, why these failures happen, and how they could be removed are all covered in the [Error Analysis](#error-analysis) below. The `TestSolverReliability` test guards a 99% reliability floor so any future regression is caught automatically.

## Error Analysis

To characterise the solver's residual failure mode, it was run against **10,000 seeds** (0–9999) from the centre-of-grid start the game uses. It filled the board completely on 9,990 — a **99.90%** success rate. The 10 failures were seeds 663, 982, 2544, 3539, 3934, 4283, 4437, 8651, 9048, and 9270.

### Methodology

The 10,000-seed sweep was run by a large language model (Claude) using a headless harness rather than the pygame window: it imports the shipping `Solver`, drives it move-by-move exactly as the live game does (same food spawning, no rendering), and records a win at 100 cells or a failure when `next_move()` returns `None` (trapped) or returns an illegal move. This is the bundled `TestSolverReliability` logic scaled from 1,000 to 10,000 seeds, instrumented to log each failure's fill level, free-cell count, head reachability, tail adjacency, cycle alignment, and shortcut share — so every figure below is measured, not estimated.

One reproducibility caveat: these are **integer** seeds (`random.seed(663)`), the convention used by the harness and the bundled `TestSolverReliability` test. The game never seeds this way — it converts every input to a string first (`random.seed("663")`), and Python produces a different number stream for an integer than for its string form. Integer seeding therefore isn't possible through the program as it stands: entered into the game these seeds become strings and play different boards that fill to 100%. The failures belong to the test's integer-seeding convention and reappear only when that harness is re-run — not during normal play.

### Why it traps — and why tail-chasing doesn't prevent it

The 10 failures are near-identical, and four shared traits explain the mechanism:

1. **It never crashes — it seals itself in.** Every failure is a "trapped" stop (the "SOLVER STOPPED" screen): no wall or self-collisions, just `next_move()` returning `None` because all four cells around the head are wall or body. The solver halts rather than make an illegal move.
2. **It traps mid-game, never at the end.** Fill at the trap averages 40% (range 28–50%) and *never* exceeds 50% — the exact point where the solver disables shortcuts and rides the pure cycle to the finish. Once on the cycle it never traps.
3. **It strands an open board.** On average 60 cells are still empty, and **none are reachable from the head.** The snake doesn't run out of room; it loses *access* to it.
4. **Its body is never cycle-aligned when it fails.** In all 10 the body is *not* a consecutive run along the Hamiltonian cycle, and the snake spent ~86% of its moves on shortcuts rather than the cycle.

These point to one cause. The "follow your tail and you can't lose" guarantee holds only while the body occupies a **consecutive run of cells on the cycle** — then the cell ahead of the head is always the one the tail is vacating, so a legal move always exists. Every shortcut steps *off* the cycle and scrambles that alignment. After enough of them the body is a tangle: the head darts into a pocket its own body then closes behind it, and the open board — including the tail's escape route — ends up on the far side of a wall of body the head can't cross. The last move attempted is always "cycle" or "tail," never "shortcut" — the trap springs exactly when the snake tries to fall back to safety and finds it gone.

So tail-chasing is a *conditional* guarantee, not an absolute one: it is safe only on the cycle, and the shortcuts that make the solver fast are departures from it. The residual 0.1% comes from three compounding limits:

- **Local checks, global failure** — each shortcut is validated alone; nothing checks the cumulative effect of many shortcuts on the body's shape.
- **A bounded horizon** — the checks see one step plus a fixed *N*-step lookahead, so a trap built up gradually forms just past what they can see.
- **No guaranteed return** — once off the cycle, re-entry needs the next cycle cell free, which nothing enforces, so the fallback may no longer be reachable.

At roughly 1 failure per 1,000 seeds, this stays comfortably within the 99% floor enforced by `TestSolverReliability`.

### Recommendations

Pushing the solver to a guaranteed 100% would mean checking after every move that the snake can still complete the board — full forward planning whose cost grows with the snake's length, exactly the overhead ruled out in [Why These Strategies](#why-these-strategies). Cheaper heuristics could narrow the gap, but only by suppressing the shortcuts that make the solver responsive — trading its speed back toward the slow, safe pure cycle — for a fractional and still unguaranteed gain. On a solver that already clears the 99% bar within a single-frame budget, that computational cost was not judged worthwhile, so the residual 0.1% was accepted.

### Two example geometries

The same mechanism — the head trapped on the wrong side of its own scrambled body — produces different shapes (`H` head, `o` body, `*` food, `.` empty):

**Seed 663 — interior self-burial.** The head is sealed inside a dense coil of its own body.

```
o o o o o o o o o o
o o o o o o o o o o
o o o o H o . . . .
o o o o o o . . . .
. . o o o o . . . .
. . o o o o . . . .
. . . . . . . . . *
. . . . . . . . . .
. . . . . . . . . .
. . . . . . . . . .
```

**Seed 982 — perimeter ring.** The body rings the boundary, stranding the head in a corner with a large but unreachable interior.

```
o o o o o o o o o o
o . . . . . . . . o
o . . . . . . . . o
o . . . . . . . . o
o . . * . . . . . o
o . . . . . . . . o
o . . . . . . . . o
o o o . . . . . . o
o o o . . . . o o o
o o o o o . . o o H
```

## Requirements

- Python 3.13
- pygame

---

## First Setup

1. Clone the repo:
   ```
   git clone https://github.com/rkdvr/snake.git
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

## Succeeding Setups

   ```
   cd snake
   conda activate snake_environment
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