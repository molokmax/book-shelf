# Specification Description

**Purpose**
Allow users to provide a URL link for a book when creating or editing a book entry via the bot.

**Requirements**
1. Add an optional `link` field to the book model (Pydantic schema). Additionally, if a book is created via a LitRes URL, that URL should be automatically attached as the book’s link.
2. Update the “add book” flow:
   - After collecting title, author, etc., ask the user for a link (optional).
   - Validate that the entered string is a well‑formed URL (http/https).
3. Update the “edit book” flow similarly, preserving the existing link if the user skips the step.
4. **Persist the new field in a SQLite database** (instead of the previous JSON file).
   - Extend the existing SQLite schema (or create a new table) to include a `link TEXT` column for books.
   - Ensure migrations are applied automatically when the bot starts (e.g., using `sqlite3` `PRAGMA user_version` or an ORM migration tool).
   - All CRUD operations in `src/core/db.py`/`src/core/repository.py` must be updated to read/write the `link` column.
5. Ensure backward compatibility – existing records without a link remain valid (the `link` column may be `NULL`).
6. Add unit‑tests covering:
   - Successful creation with a link.
   - Creation without a link.
   - Editing to add or change a link.
   - Validation rejects malformed URLs.
   - Database migration creates the new column without data loss.

**Dependencies**
None (this is the first artifact, so no prior artifacts must be completed).

**Template**
Provide a concise markdown description of the change, then list the concrete tasks you plan to implement for the next artifact (e.g., design‑proposal).