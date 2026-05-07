# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

- **Install dependencies**: `pip install -r requirements.txt`
- **Run the bot**: `python src/main.py` (ensure `BOT_TOKEN` environment variable is set, e.g., `export BOT_TOKEN=your_token` on *nix or `set BOT_TOKEN=your_token` on Windows)
- **Run all tests**: `pytest`
- **Run a single test file**: `pytest tests/test_book_add.py`
- **Run a single test case**: `pytest tests/test_book_add.py::test_add_book_success`
- **Lint the code**: `flake8 src/`
- **Check coverage**: `coverage run -m pytest && coverage report`

## High‑Level Architecture

- **src/main.py** – Entry point that creates and runs `BookShelfBot`.
- **src/vk_main.py** – Entry point that creates and runs `VkBookShelfBot`.
- **src/bot/** – Telegram bot layer:
  - `bot.py` contains `BookShelfBot`, which sets up the `python‑telegram‑bot` `Application`, loads configuration, and registers handlers.
  - `handlers/` are split by concern:
    - `commands.py` – top‑level commands (`/start`, `/help`, `/cancel`).
    - `messages.py` – generic text handling.
    - `callbacks.py` – callback‑query handling.
    - `book/` – CRUD‑style handlers for books (`add`, `list`, `edit`, `delete`, `progress`, `stats`, `export`).
  - `keyboards/` – UI keyboard layouts used by the bot.
- **src/vk_bot/** – Vk bot layer:
  - `bot.py` contains `VkBookShelfBot`, which uses `vk_api`, loads configuration, and runs handlers.
  - `handlers/` are split by use cases. Each file in this folder is responsible for some command (`start`, `add`, `edit`, `list`).
  - `keyboards.py` – Shared keyboard layouts used by the several commands. Specific keyboards should be in command handler file.
- **src/core/** – Core application logic, independent of Telegram:
  - `models.py` – Pydantic data models for books and related entities.
  - `database.py` – Simple JSON‑file based persistence (loads/saves `data/books.json`).
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

## Important Files

- `README.md` – High‑level project description and feature list.
- `docs/project_structure.md` – Detailed directory overview (mirrored above).
- `requirements.txt` – Python dependencies, including `pydantic`, `pytest`, `flake8`, etc.

## Implementation Tips
- В сообщениях обращайся к пользователю на "ты"
- Комментарии в коде пиши на русском языке

## Development Tips

- Keep configuration values in a `.env` file (ignored by git) and load them with `python-dotenv`.
- When adding new functionality, place bot‑related code in `src/bot/handlers/` and core logic in `src/core/` to maintain separation.
- Run the test suite frequently (`pytest -x`) to catch regressions early.
- Use the provided keyboards for consistent UI layout across new commands.
