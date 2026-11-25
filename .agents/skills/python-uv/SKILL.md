---
name: python-uv
description: >-
  Use whenever managing Python environments, installing or removing Python
  dependencies, or running Python scripts/tools in this project. Enforces using
  `uv` and `uv add` (never `uv pip` or bare `pip`).
---

# Python Dependency Management with `uv`

Always use `uv` for Python environments, dependency management, and script execution in this project.

## Rules

1. **Always use `uv add` for dependencies** — never use `uv pip install`, `uv pip ...`, or bare `pip install`.
   - Runtime dependency: `uv add <package>`
   - Dev/test dependency: `uv add --dev <package>`
   - Remove dependency: `uv remove <package>`
2. **Initialize `pyproject.toml` first** if not yet present:
   - `uv init --no-workspace` (or `uv init`)
3. **Run scripts and tools via `uv run`**:
   - `uv run python src/scanner.py --help`
   - `uv run pytest`
4. **Sync environments with `uv sync`** rather than manually installing from requirements files.
5. **Raspberry Pi system bindings (`picamera2` / `libcamera`)**:
   - On Raspberry Pi OS where `python3-picamera2` is provided via `apt`, create the virtual environment with `uv venv --system-site-packages` so `uv run` can import system `picamera2` while still managing all project dependencies with `uv add`.
