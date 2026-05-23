## 1. Setup and Navigation

- [x] 1.1 Add `details` button to main_keyboard in `src/bot/keyboards.py`.
- [x] 1.2 Create new handler file `src/bot/handlers/details.py` with entry point `handle_details`.
- [x] 1.3 Register the `/details` command in `src/bot/bot.py` (or appropriate dispatcher).

## 2. Handler Logic

- [x] 2.1 Implement logic to send a numbered list of books when the user invokes `/details`.
- [x] 2.2 Add input validation to ensure the user selects a valid number; request re‑entry on error.
- [x] 2.3 Retrieve the selected book using existing service (`BookService.get_book_by_id`).
- [x] 2.4 Format and send the detailed information message (title, author, tags, status, total pages, pages read, date added, start date, link).

## 3. Integration and UI

- [x] 3.1 Update any relevant keyboards or reply markup to include the new `details` button.

## 4. Testing

- [x] 4.1 Add unit tests for the new handler in `tests/handlers/test_details.py` covering list generation, number selection, and message formatting.
- [x] 4.2 Update existing test suites to accommodate the new keyboard if needed.

## 5. Documentation

- [x] 5.1 Update `README.md` or command help to describe the new `/details` command.
- [x] 5.2 Document any new settings or environment variables (if applicable) in `docs/`.
