# Spec Delta

## MODIFIED Requirements

### Requirement: Successful progress update

The system SHALL apply the progress value and show the existing progress summary after a successful update. New achievements SHALL appear as one block after the daily-goal block, or after the progress summary if no goal is set.

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

#### Scenario: New achievement after a daily-goal block

- **WHEN** the progress update completes a daily goal and unlocks an achievement
- **THEN** the final message SHALL contain the daily-goal congratulation followed by the new-achievement block.

#### Scenario: New achievement without a daily goal

- **WHEN** the progress update unlocks an achievement and the user has no daily goal
- **THEN** the final message SHALL contain the new-achievement block after the progress summary.

#### Scenario: Several achievements unlocked

- **WHEN** one progress update unlocks several achievements
- **THEN** the final message SHALL list all of them in one new-achievement block.

#### Scenario: Retrospective achievement without a page change

- **WHEN** the submitted page is unchanged but the progress check unlocks a retrospective achievement
- **THEN** the final message SHALL contain the unchanged-progress notice and the new-achievement block.

#### Scenario: No achievements unlocked

- **WHEN** the progress update does not unlock any achievements
- **THEN** the final message SHALL NOT contain a new-achievement block.
