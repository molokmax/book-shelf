## Context

The change adds an optional `link` field to the book model, updates add/edit flows to capture and validate a URL, stores data in SQLite (including migration adding `link TEXT`), and automatically attaches a LitRes URL when a book is created from such a link. This impacts the data model, repository, DB layer, and bot handlers.

## Goals / Non-Goals

**Goals:**
- Persist book link information reliably in SQLite.
- Provide a seamless user experience for adding/editing links.
- Auto‑attach LitRes URLs during creation.
- Maintain backward compatibility with existing records.

**Non-Goals:**
- Implement a full web UI for link management (outside bot scope).
- Support non‑HTTP protocols for links.

## Decisions

- Use a simple schema migration that adds a nullable `link TEXT` column to the `books` table.
- Leverage Python's `urllib.parse` for URL validation.
- Extend Pydantic `Book` model with an optional `link: HttpUrl | None` field.
- In add/edit handlers, after the main data collection, prompt the user for a link; skip if empty.
- When adding a book via the `add_litres` command, automatically set the `link` field to the provided LitRes URL.

## Risks / Trade-offs

- **Risk:** Migration may fail on existing databases with corrupted data.
  - **Mitigation:** Wrap migration in a try/except, log errors, and fallback to creating a fresh DB if migration is impossible.
- **Risk:** URL validation may reject some legitimate links.
  - **Mitigation:** Use `HttpUrl` validation and allow users to skip the field.
- **Risk:** Adding a new column could affect queries assuming a fixed set of columns.
  - **Mitigation:** Update all query builders to explicitly select needed columns.
