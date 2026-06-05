## ADDED Requirements

### Requirement: Routing Refactor Capability
The system SHALL provide a structured command routing mechanism with priority handling and state management for each user.

#### Scenario: Route command to appropriate handler
- **WHEN** a user sends a command that matches a registered handler's command list
- **THEN** the CommandRouter SHALL invoke the first handler (by priority) whose `can_handle` returns true.

#### Scenario: Prioritized handling
- **WHEN** multiple handlers can handle the same command
- **THEN** the CommandRouter SHALL select the handler with the highest priority value.

#### Scenario: State persistence
- **WHEN** a handler updates the user state
- **THEN** the UserStateRepository SHALL persist the state in the SQLite `user_state` table.
