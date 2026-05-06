# Telegram Bot Use Cases

The Book Shelf Telegram bot provides a set of commands and interactive flows that cover the entire lifecycle of managing a personal reading list. Below is a concise list of the supported use cases, derived from the handler implementations in `src/bot/`.

---

## 1. Bot Lifecycle
- **/start** – Greets the user and displays the main menu with available commands.
- **/help** – Shows detailed help text describing all commands and features.
- **/cancel** – Cancels any ongoing multi‑step operation and returns to the main menu.

## 2. Book Management
### Adding Books
- **/add** – Starts the "add book" flow.
  - **Manual entry** – User provides title, author, tags, and page count step‑by‑step.
  - **LitRes import** – User supplies a LitRes URL, the bot parses the page and returns book details for confirmation before adding.

### Listing Books
- **/list** – Displays the user's library, sorted by status, with formatted book information.

### Editing Books
- **/edit** – Allows selection of a book and editing of its tags.

### Deleting Books
- Inline callback **Delete** – Removes a selected book from the library.

## 3. Reading Progress & Status
- **/progress** (via inline button) – Prompts the user to enter the current page number and updates the reading progress.
- **Status change** (inline callback) – Lets the user set a book’s status to one of:
  - "Want to read"
  - "Reading now"
  - "Read"
  - "Postponed"

## 4. Statistics & Export
- **/stats** – Shows aggregated reading statistics (total books, read books, pages, average progress, etc.).
- **/export** – Generates a CSV file with the full library data and sends it to the user.

## 5. Miscellaneous
- **Keyboard navigation** – Main menu, cancel keyboards, and context‑specific inline keyboards guide the user through each flow.
- **Logging** – All handlers log actions via `utils.logger.setup_logger` for debugging and audit purposes.

---

These use cases collectively enable a user to track, organize, and analyze their reading habits directly from Telegram.
