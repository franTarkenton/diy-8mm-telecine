# Project Rules — DIY Standard 8mm Telecine

- **Archive, never delete, older plans and layouts:** When replacing or superseding design plans, diagrams, build guides, or layout files, always move the older versions into a versioned archive directory (`docs/v1/`, `docs/v2/`, etc.) rather than deleting them. Follow the `archive-older-plans` skill in `.agents/skills/archive-older-plans/SKILL.md`.
- **Always use `uv` (and `uv add`) for Python dependencies:** Never use bare `pip` or legacy `uv pip ...` commands. Use `uv add` / `uv add --dev` to add dependencies, `uv remove` to remove them, `uv sync` to sync, and `uv run` to execute Python scripts. Follow the `python-uv` skill in `.agents/skills/python-uv/SKILL.md`.
