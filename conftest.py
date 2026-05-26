"""
conftest.py — pytest configuration for the Snake project.

This file is automatically loaded by pytest before any test runs.
Its sole responsibility is adding src/ to sys.path so that every
test file can import project modules directly:

    import snake_pygame
    from constants import COLS
    from solver_algorithm import Solver

Without this file each test would need its own sys.path.insert() call.
Placing it at the project root means it applies to all tests under
tests/ regardless of how deeply nested they are.

No fixtures are defined here.  Game-specific fixtures (headless pygame
setup, pre-built Solver instances, etc.) live in the individual test
files or in tests/conftest.py if they need to be shared across suites.
"""

import sys
import os

# Add src/ to the front of the path so project imports take priority
# over any same-named packages that might be installed system-wide.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))