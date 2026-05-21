## ADDED Requirements

### Requirement: Book link support
The system SHALL allow a book entry to have an optional external link associated with it.

#### Scenario: Adding a book with a link via add command
- **WHEN** the user provides a valid URL in the link prompt during the add book flow
- **THEN** the system stores the URL in the `link` field of the book record in SQLite.

#### Scenario: Adding a book without a link
- **WHEN** the user skips the link prompt or provides an empty value
- **THEN** the `link` field is stored as NULL.

#### Scenario: Adding a book using the `add_litres` command
- **WHEN** the user invokes the `add_litres` command with a LitRes URL
- **THEN** the system automatically sets the `link` field to the provided LitRes URL.

#### Scenario: Editing a book to add, change, or keep existing link
- **WHEN** the user edits an existing book and is prompted for a link, they can either provide a new valid URL, leave the field empty, or press a "Next" button to keep the current link unchanged
- **THEN** the system retains the existing `link` value if "Дальше" is pressed, stores a new URL if provided, or sets the field to NULL if the user explicitly clears it
- **WHEN** the user edits an existing book and provides a new valid URL
- **THEN** the system updates the `link` field with the new URL.

#### Scenario: Validation of malformed URLs
- **WHEN** the user provides a string that is not a valid HTTP/HTTPS URL
- **THEN** the system prompts the user to correct the input and does not store the value.
