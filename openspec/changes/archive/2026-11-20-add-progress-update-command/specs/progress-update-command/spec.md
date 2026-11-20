## ADDED Requirements

### Requirement: Progress command entry point

The system SHALL provide a `/progress` command with aliases `progress` and `прогресс` for updating reading progress.

#### Scenario: User invokes the command

- **WHEN** the user sends `/progress`, `progress` or `прогресс` without an active scenario
- **THEN** the system SHALL start the progress update scenario.

#### Scenario: Command is discoverable

- **WHEN** the user opens the main keyboard or reads `/start` or `/help`
- **THEN** the system SHALL show `/progress` among the available commands.

### Requirement: Default reading book selection

The system SHALL show books with status `reading` immediately after the `/progress` command starts.

#### Scenario: Reading books exist

- **WHEN** the user starts `/progress` and has books with status `reading`
- **THEN** the system SHALL send a numbered list of those books ordered by `updated_at` descending
- **AND** the keyboard SHALL contain `Другие` and `Отмена`.

#### Scenario: Only one reading book exists

- **WHEN** the user has exactly one book with status `reading`
- **THEN** the system SHALL still show the numbered list with that book.

#### Scenario: No reading books exist

- **WHEN** the user starts `/progress` and has no books with status `reading`
- **THEN** the system SHALL show a message that there are no books with status `«Читаю»`
- **AND** the system SHALL immediately show the standard filter keyboard.

#### Scenario: User selects a reading book

- **WHEN** the user enters a valid number from the reading book list
- **THEN** the system SHALL show the progress input prompt for the selected book without an intermediate action menu.

### Requirement: Standard book selection via Другие

The system SHALL allow the user to select any book through the `Другие` button using the standard filter dialog.

#### Scenario: User opens the standard dialog

- **WHEN** the user presses `Другие`
- **THEN** the system SHALL show filters `По статусу`, `По тегам` and `Все`.

#### Scenario: User filters by status

- **WHEN** the user selects `По статусу` and a status
- **THEN** the system SHALL show a numbered list of the user's books with that status.

#### Scenario: User filters by tag

- **WHEN** the user selects `По тегам` and a tag
- **THEN** the system SHALL show a numbered list of the user's books with that tag.

#### Scenario: User selects all books

- **WHEN** the user selects `Все`
- **THEN** the system SHALL show a numbered list of all the user's books with read books last.

#### Scenario: User selects a book from the standard dialog

- **WHEN** the user enters a valid number from a filtered list
- **THEN** the system SHALL show the progress input prompt for the selected book.

#### Scenario: Filtered list is empty

- **WHEN** the selected filter returns no books
- **THEN** the system SHALL show a message that no books were found
- **AND** the system SHALL return the user to the main keyboard.

#### Scenario: User cancels

- **WHEN** the user presses `Отмена` at any step
- **THEN** the system SHALL cancel the progress scenario and return the user to the main keyboard.

### Requirement: Progress input and confirmation

The system SHALL validate the entered progress value and preserve the current state after invalid input.

#### Scenario: Valid value is entered

- **WHEN** the user enters an integer from 0 to the total number of pages
- **THEN** the system SHALL accept the value for further processing.

#### Scenario: Non-integer value is entered

- **WHEN** the user enters a value that is not an integer
- **THEN** the system SHALL send `⚠️ Не удалось обработать сообщение.` with a hint to enter a number
- **AND** the system SHALL keep the progress state active.

#### Scenario: Value is out of range

- **WHEN** the user enters a negative value or a value greater than the total number of pages
- **THEN** the system SHALL send `⚠️ Не удалось обработать сообщение.` with an explanation of the valid range
- **AND** the system SHALL keep the progress state active.

#### Scenario: Progress rollback is detected

- **WHEN** the new value is less than the current progress
- **THEN** the system SHALL ask for confirmation before applying the value.

#### Scenario: Progress jump is detected

- **WHEN** the new value exceeds the current progress by more than the reading speed or a significant share of the book
- **THEN** the system SHALL ask for confirmation before applying the value.

#### Scenario: User confirms a suspicious value

- **WHEN** the user presses `Продолжить` or enters another valid value during confirmation
- **THEN** the system SHALL apply the chosen value according to the existing rules.

### Requirement: Successful progress update

The system SHALL apply the progress value and show the existing progress summary after a successful update.

#### Scenario: Progress is updated

- **WHEN** the user submits an accepted progress value
- **THEN** the system SHALL save the new current page
- **AND** the system SHALL record the number of newly read pages in reading statistics
- **AND** the system SHALL show the progress summary with weekly, monthly and average reading data
- **AND** the system SHALL return the user to the main keyboard.

#### Scenario: Progress did not change

- **WHEN** the user submits the current page again
- **THEN** the system SHALL show a notice that progress did not change
- **AND** the system SHALL show the progress summary
- **AND** the system SHALL return the user to the main keyboard.

#### Scenario: Book is completed

- **WHEN** the new current page equals the total number of pages
- **THEN** the system SHALL set the book status to `read` according to the existing status rules.

#### Scenario: Book was not being read

- **WHEN** the user updates progress on a book with status `want_to_read` and the new current page is greater than 0
- **THEN** the system SHALL set the book status to `reading` according to the existing status rules
- **AND** the system SHALL NOT change the status of `postponed` or `read` books unless the existing rules require it.

### Requirement: Cross-command routing

The `/progress` command SHALL NOT take control away from an active scenario of another command.

#### Scenario: Another command is active

- **WHEN** the user sends `/progress` while another command has an active state
- **THEN** `ProgressHandler` SHALL NOT change that state
- **AND** the text SHALL be processed by the active command handler as ordinary input.

#### Scenario: Progress command is active

- **WHEN** the user sends `/progress` while the progress scenario is already active
- **THEN** the current progress step SHALL process the text as invalid input
- **AND** the system SHALL send the standard invalid input message.

### Requirement: Edit command cleanup and legacy compatibility

The system SHALL remove progress from the `/edit` action menu while temporarily supporting existing progress states.

#### Scenario: User selects a book in edit

- **WHEN** the user opens the action menu for a book in `/edit`
- **THEN** the keyboard SHALL NOT contain a `Прогресс` button.

#### Scenario: User enters an unknown action in edit

- **WHEN** the user enters text that does not match `Изменить`, `Статус`, `Удалить` or `Отмена`
- **THEN** the system SHALL send `⚠️ Выбери действие`
- **AND** the system SHALL show the book action keyboard again.

#### Scenario: User continues a legacy progress flow

- **WHEN** the user has an active `/edit` state `waiting_for_progress_input` or `waiting_for_progress_confirm`
- **THEN** the system SHALL process the input through the shared progress update flow.
