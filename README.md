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
| Pygame | Arrow keys | Steer the snake |
| Pygame | R | Restart (game over screen) |
| Solver | Space | Pause / resume |
| Solver | R | Restart |
| Solver | + / = | Speed up |
| Solver | - | Slow down |

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

---

## Project Structure

```
snake/
├── src/
│   ├── constants.py          grid dimensions, cell size, direction definitions
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