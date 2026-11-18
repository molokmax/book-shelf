# AGENTS.md

This file provides guidance to Open Code when working with code in this repository.

## Common Development Commands

- **Install dependencies**: `pip install -r requirements.txt`
- **Run the bot**: `python src/main.py` (ensure `BOT_TOKEN` environment variable is set, e.g., `export BOT_TOKEN=your_token` on *nix or `set BOT_TOKEN=your_token` on Windows)
- **Run all tests**: `pytest`
- **Run a single test file**: `pytest tests/test_book_add.py`
- **Run a single test case**: `pytest tests/test_book_add.py::test_add_book_success`
- **Lint the code**: `flake8 src/`
- **Check coverage**: `coverage run -m pytest && coverage report`

## High‑Level Architecture

- **src/main.py** – Entry point that creates and runs `VkBookShelfBot`.
- **src/vk_bot/** – Vk bot layer:
  - `bot.py` contains `VkBookShelfBot`, which uses `vk_api`, loads configuration, and runs handlers.
  - `command_router.py` – `CommandRouter` — central command router with priority‑based handler dispatching.
  - `handlers/base.py` – `AbstractCommandHandler` base class with `can_handle`, `priority`, `commands`; `handle()` is a template method that rejects commands while another scenario is active.
  - `handlers/scenario.py` – `ScenarioHandler` base class for multi-step commands: state registry, `start`/`begin`/`goto`/`finish`, `step_<state>` and `render_<state>` conventions.
  - `states.py` – `StrEnum` names of scenario steps (shared sub-scenario steps and per-command steps).
  - `handlers/` – directory with command handlers. Each file is a single handler (`add.py`, `edit.py`, `list.py`, etc.) with a class inheriting `AbstractCommandHandler` or `ScenarioHandler`.
  - `core/repository.py` – `UserStateRepository` for persisting user state in SQLite (`user_state` table).
  - `keyboards.py` – Shared keyboard layouts used by the several commands. Specific keyboards should be in command handler file.
- **src/core/** – Core application logic, independent of Telegram:
  - `models.py` – Pydantic data models for books and related entities.
  - `database.py` – SQLite‑based persistence (stores data in `data/database.db`).
  - `db.py` – Low‑level database operations.
  - `repository.py` – Repository pattern exposing high‑level data access methods.
  - `services.py` – Business‑logic services (e.g., adding a book, updating status).
- **src/utils/** – Helper utilities:
  - `config.py` – Loads configuration from environment variables (`BOT_TOKEN`, optional `DATA_DIR`, `DEBUG`).
  - `logger.py` – Central logging configuration.
  - `helpers.py` – Miscellaneous helper functions used across the codebase.
  - `litres_parser.py` – HTML parser for extracting book data from LitRes.
- **data/** – Runtime data storage.
- **tests/** – Pytest test suite covering handlers, services, and parsers.

## Git Conventions

- Branch naming: `<type>/<issue-number>/<slug>`, where `<type>` is `feature` for features, `fix` for bug fixes, `chore` for maintenance, and `<slug>` is a short lowercase summary of the issue with hyphens. Examples: `feature/73/shorten-main-keyboard`, `fix/51/slow-queries`, `chore/ci-updates`.

## Important Files

- `README.md` – High‑level project description and feature list.
- `requirements.txt` – Python dependencies, including `pydantic`, `pytest`, `flake8`, etc.
- `pyproject.toml` – Shared config for black, isort, pytest.
- `.flake8` – Flake8 config (line-length и правила согласованы с black).

## Implementation Tips
- Address the user informally ("ты") in messages
- Write code comments in Russian
- Use relative imports when referencing modules within the same package
- Always place imports at the top of the file, never inline
- Multi-step commands inherit `ScenarioHandler`, not `AbstractCommandHandler`. Declare the step enum (`states`), `initial_state`, `scenario_command`, and a `step_<state>(context, state_info)` method per step; add `render_<state>(context, state_info)` to send the prompt. A step returns the next state name, or `None` to stay in the current step. `__init_subclass__` fails on import if a `step_*` method is missing. Use `begin()` to start a scenario, `goto()` to move to a state, `finish()` to send the final message and delete the state (in that order), and `reset_unknown_state()` is called automatically for unknown steps.
- Do not implement the foreign-scenario guard by hand: `AbstractCommandHandler.handle()` is a template method. Any non-system handler gets a refusal message when `state["command"]` belongs to another handler. Mark global commands with `is_system = True` (only `/start` and `/cancel`) and set `scenario_command` to the canonical command written into `state["command"]`. Re-entering the handler's own command (payload command without `action`, or text starting with `/`) restarts the scenario. The router keeps two passes: by the typed command, then by the state's command for free-text steps.
- After completing changes, run: `isort .`, `black .`, `flake8 src/`, and `pytest`

## Development Tips

- Keep configuration values in a `.env` file (ignored by git) and load them with `python-dotenv`.
- When adding new functionality, place bot‑related code in `src/vk_bot/handlers/` and core logic in `src/core/` to maintain separation.
- Run the test suite frequently (`pytest -x`) to catch regressions early.
- Use the provided keyboards for consistent UI layout across new commands.
