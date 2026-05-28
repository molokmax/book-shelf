## ADDED Requirements

### Requirement: filter-books-list
The system SHALL allow users to filter the list of books by status or tags via interactive keyboards in the bot.

#### Scenario: Filter by status
- **WHEN** user selects "По статусу" from the filter keyboard
- **THEN** bot requests a status selection and displays only books matching the chosen status.

#### Scenario: Filter by tags
- **WHEN** user selects "По тегам" from the filter keyboard
- **THEN** bot requests a tag selection and displays only books that have the selected tag.
