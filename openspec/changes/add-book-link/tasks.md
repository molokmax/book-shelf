## 1. Model and Database Updates

- [x] 1.1 Add optional `link` field to the Pydantic `Book` model in `src/core/models.py`
- [x] 1.2 Create SQLite migration to add nullable `link TEXT` column to the `books` table
- [x] 1.3 Update repository methods in `src/core/repository.py` to handle the new column (read/write)

## 2. Bot Handlers – Add/Edit Flow

- [x] 2.1 Modify the add‑book handler to ask for a link after other fields and validate it as an HTTP/HTTPS URL
- [x] 2.2 Modify the edit‑book handler to prompt for a link with options: new URL, keep existing (via "Next" button), or clear
- [x] 2.3 Integrate automatic link assignment in the `add_litres` command: set `link` to the provided LitRes URL

## 3. Validation and Utilities

- [x] 3.1 Implement URL validation helper (e.g., using `pydantic.HttpUrl` or `urllib.parse`)
- [x] 3.2 Ensure that malformed URLs trigger a retry prompt in the bot

## 4. Tests

- [x] 4.1 Add unit tests for creating a book with a valid link
- [x] 4.2 Add unit tests for creating a book without a link (link = NULL)
- [x] 4.3 Add unit tests for editing a book to change, keep, or clear the link
- [x] 4.4 Add integration test for `add_litres` command automatically setting the link

## 5. Documentation

- [x] 5.1 Update README or bot help text to mention the new link functionality
- [x] 5.2 Document migration steps for existing deployments
