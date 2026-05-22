## Why

Пользователь хочет иметь возможность перейти по ссылке для покупки книги или уточнения информации о ней.

## What Changes

- Add optional `link` field to the book model.
- Update add/edit book flows to request and validate a URL.
- Store book data, including the link, in SQLite (migration adds `link TEXT`).
- If a book is created via a LitRes URL, automatically attach that URL as the book’s link.
- Update CRUD operations to handle the new column.
- Add unit‑tests covering creation, editing, validation, and migration.

## Capabilities

### New Capabilities
- `book-link`: Enables attaching an external URL to a book entry and persisting it in SQLite.

### Modified Capabilities
- `book-management`: Adjust requirements to include optional link handling and SQLite persistence.

## Impact

- Core data model (`src/core/models.py`) and repository (`src/core/repository.py`).
- Database layer (`src/core/db.py`) – schema migration.
- Bot handlers for add/edit (`src/bot/handlers/book/*.py`).
- Tests (`tests/test_book_add.py`, etc.).
