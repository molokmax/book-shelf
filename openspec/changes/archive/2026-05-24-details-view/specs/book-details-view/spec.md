## ADDED Requirements

### Requirement: User can view detailed information about a selected book via the `/details` command
The system SHALL allow a user to retrieve full details of any book in their collection by invoking the `/details` command.

#### Scenario: User selects a book number from the presented list
- **WHEN** the user presses the `/details` button, the bot sends a numbered list of books.
- **AND** the user replies with the number corresponding to the desired book.
- **THEN** the bot retrieves the book record and sends a message containing the following fields: title, author, tags, status, total pages, pages read, date added, date reading started, and link.
