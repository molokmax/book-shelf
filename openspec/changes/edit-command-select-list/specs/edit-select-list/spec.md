## ADDED Requirements

### Requirement: edit-filter-options
The system SHALL present the user with a filter selection when the `/edit` command is issued, offering three filtering modes: "by status", "by tag", and "all".

#### Scenario: User chooses filter mode
- **WHEN** the user issues the `/edit` command
- **THEN** the bot SHALL ask the user to choose a filter mode: "by status", "by tag", or "all".
- **AND** if the user selects "by status"
- **THEN** the bot SHALL present a list of available book statuses (e.g., "read", "planned", "wishlist") for selection.
- **AND** if the user selects "by tag"
- **THEN** the bot SHALL present a list of tags that are currently used in the library.
- **AND** after the user makes a selection (or chooses "all"), the bot SHALL display the list of books filtered according to the chosen criterion for further editing.
