## 1. Setup

- [x] 1.1 Создать модуль `src/vk_bot/command_router.py` и добавить класс `CommandRouter`.
- [x] 1.2 Добавить базовый класс `src/vk_bot/handlers/base.py` (`AbstractCommandHandler`).
- [x] 1.3 Реализовать репозиторий `src/vk_bot/repository/user_state.py` с методами `get_state` и `save_state`.

## 2. Core Implementation

- [x] 2.1 Переписать обработчик `add.py` как наследника `AbstractCommandHandler`, реализовать шаги (`ask_title`, `ask_author`, `confirm` и т.д.).
- [x] 2.2 Переписать остальные обработчики (`edit.py`, `list.py`, `details.py` и т.д.) аналогично.
- [x] 2.3 В `CommandRouter.register_handler` добавить все новые обработчики с корректными приоритетами.
- [x] 2.4 Обновить `src/vk_bot/bot.py` – инициализировать `CommandRouter`.

## 3. Migration

- [x] 3.1 Добавить миграцию SQLite для таблицы `user_state` (колонки `user_id TEXT PRIMARY KEY, json TEXT`).
- [x] 3.2 Обновить `src/core/database.py`/`src/core/db.py` для выполнения новой миграции при старте.

## 4. Tests

- [x] 4.1 Добавить unit‑тесты для `CommandRouter` (правильный порядок по приоритету, `can_handle`).
- [x] 4.2 Добавить тесты для `AbstractCommandHandler`‑наследников (проверка шагов и сохранения состояния).
- [x] 4.3 Обновить существующие тесты `tests/handlers/*` под новую структуру.
- [x] 4.4 Запустить `pytest -x` и убедиться, что все тесты проходят.

## 5. Documentation

- [x] 5.1 Обновить `README.md` раздел "Architecture" с описанием нового роутинга.
- [x] 5.2 Обновить `AGENTS.md` и `CLAUDE.md` при необходимости.
