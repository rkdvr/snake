"""
main.py — Entry point for the Snake project.

Presents a menu to choose between the three game modes and handles the
"Solve this seed?" flow between the playable game and the AI solver.

Usage
-----
    python main.py

Menu options
------------
    1  Basic   — terminal Snake (WASD controls, no dependencies beyond Python)
    2  Pygame  — playable Snake with a pygame window
    3  Solver  — AI solver using a Hamiltonian cycle
    q  Quit

Solve-this-seed flow
--------------------
After the pygame game window is closed, the seed used for that session is
offered to the solver automatically:

    Game ended — seed: erika
    Solve this seed? (Y/n): y   ← launches solver with seed "erika"

This lets you compare your own route against the AI's on exactly the same
board.  The solver receives the seed as a constructor argument and
reproduces the same food sequence without any extra setup.

Path setup
----------
This file inserts src/ into sys.path so all project modules are importable
regardless of the working directory.  conftest.py does the same for pytest,
so the two files share the same strategy but serve different contexts.
"""

import sys
import os

# Make all modules in src/ importable (mirrors conftest.py for the test suite)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))


# ── Menu ──────────────────────────────────────────────────────────────────────

def _print_menu(session_seed: str | None = None) -> None:
    print()
    print("  Snake")
    print("  " + "─" * 25)
    print("  1   Basic       (terminal)")
    print("  2   Pygame      (playable)")
    print("  3   Solver      (AI)")
    print("  q   Quit")
    if session_seed:
        print(f"\n  Session seed: {session_seed}")
    print()


# ── Mode runners ──────────────────────────────────────────────────────────────

def _run_basic(suggested_seed: str | None = None) -> str | None:
    """Launch the terminal Snake game.  Returns the seed used."""
    from snake_basic import main
    return main(suggested_seed=suggested_seed)


def _run_pygame(suggested_seed: str | None = None) -> str | None:
    """
    Launch the playable pygame Snake game.  Returns the seed used.

    After the window closes, offer to hand the session seed to the solver
    so the user can watch the AI play the exact same board.
    """
    from snake_pygame import SnakeGame

    game = SnakeGame(suggested_seed=suggested_seed)
    seed, solve_now = game.run()   # returns (seed, True) if S was pressed

    if solve_now:
        _run_solver(seed=seed)
        return seed

    print(f"\n  Game ended — seed: {seed}")
    try:
        answer = input("  Solve this seed? (Y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"

    if answer in ("", "y", "yes"):
        _run_solver(seed=seed)
    return seed


def _run_solver(seed: str | None = None, suggested_seed: str | None = None) -> str | None:
    """
    Launch the AI solver game.  Returns the seed used.

    Parameters
    ----------
    seed : str or None
        When called after _run_pygame(), the pygame session seed is passed
        directly so the solver reproduces the same board without prompting.
    suggested_seed : str or None
        Shown as the default prompt value when no explicit seed is given.
        Used to carry the session seed across modes.
    """
    from snake_solver import SnakeSolverGame

    game = SnakeSolverGame(seed=seed, suggested_seed=suggested_seed)
    return game.run()


# ── Main loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    """Run the main menu loop until the user quits."""
    print("\n  Welcome to Snake.")
    session_seed: str | None = None

    while True:
        _print_menu(session_seed)

        try:
            choice = input("  Choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye.")
            break

        if choice == "1":
            seed = _run_basic(suggested_seed=session_seed)
            if seed:
                session_seed = str(seed)

        elif choice == "2":
            seed = _run_pygame(suggested_seed=session_seed)
            if seed:
                session_seed = str(seed)

        elif choice == "3":
            seed = _run_solver(suggested_seed=session_seed)
            if seed:
                session_seed = str(seed)

        elif choice in ("q", "quit", "exit", ""):
            print("\n  Goodbye.")
            break

        else:
            print(f"\n  Unknown option '{choice}' — enter 1, 2, 3, or q.")


if __name__ == "__main__":
    main()