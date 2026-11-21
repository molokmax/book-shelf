## ADDED Requirements

### Requirement: details-filter capability
The system SHALL provide an interactive filtering layer for the `details` command, allowing users to filter books by status or tag before displaying the list.

#### Scenario: User applies status filter
- **WHEN** the user selects a status filter in the interactive UI
- **THEN** the system SHALL display only books matching the selected status.

#### Scenario: User applies tag filter
- **WHEN** the user selects a tag filter in the interactive UI
- **THEN** the system SHALL display only books matching the selected tag.

#### Scenario: User requests all books
- **WHEN** the user clicks the "Все" button
- **THEN** the system SHALL display the full list of books without any filter applied.
