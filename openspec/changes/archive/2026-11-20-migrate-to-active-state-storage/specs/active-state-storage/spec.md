# Specification for active-state-storage

## ADDED Requirements

### Requirement: UserStateRepository SHALL be in core.repository
`UserStateRepository` SHALL be moved from `vk_bot/repository/user_state.py` to `core/repository.py` and follow the same DI pattern as other repositories (accept optional `db` parameter).

#### Scenario: Repository is importable from core
- **WHEN** code imports `UserStateRepository` from `core.repository`
- **THEN** the import SHALL succeed

#### Scenario: Repository follows DI pattern
- **WHEN** `UserStateRepository` is instantiated without arguments
- **THEN** it SHALL create its own `Database` instance
- **WHEN** `UserStateRepository` is instantiated with a `db` argument
- **THEN** it SHALL use the provided `Database` instance

### Requirement: Repository SHALL support delete
`UserStateRepository` SHALL have a `delete_state(user_id: str) -> None` method that removes the state record for the given user.

#### Scenario: Delete existing state
- **WHEN** `delete_state` is called for a user who has a state record
- **THEN** the record SHALL be removed from the `user_state` table

#### Scenario: Delete non-existent state
- **WHEN** `delete_state` is called for a user without a state record
- **THEN** no error SHALL be raised

### Requirement: ActiveStateStorage SHALL wrap UserStateRepository
`ActiveStateStorage` SHALL provide a high-level interface over `UserStateRepository` with methods: `get`, `save`, `delete`, `is_active`, `get_command`, `get_current_state`, `new_state`.

#### Scenario: Get state returns dict
- **WHEN** `get(user_id)` is called for a user with no state
- **THEN** it SHALL return an empty dict
- **WHEN** `get(user_id)` is called for a user with saved state
- **THEN** it SHALL return the saved dict

#### Scenario: Save persists state
- **WHEN** `save(user_id, state_dict)` is called
- **THEN** subsequent `get(user_id)` SHALL return the same dict

#### Scenario: Delete removes state
- **WHEN** `delete(user_id)` is called after saving state
- **THEN** subsequent `is_active(user_id)` SHALL return `False`

#### Scenario: is_active checks non-empty state
- **WHEN** user has no state record
- **THEN** `is_active(user_id)` SHALL return `False`
- **WHEN** user has a non-empty state dict
- **THEN** `is_active(user_id)` SHALL return `True`
- **WHEN** user has an empty state dict `{}`
- **THEN** `is_active(user_id)` SHALL return `False`

#### Scenario: get_command extracts command
- **WHEN** state has `{"command": "/add", ...}`
- **THEN** `get_command(user_id)` SHALL return `"/add"`
- **WHEN** state is empty
- **THEN** `get_command(user_id)` SHALL return `None`

#### Scenario: get_current_state extracts step
- **WHEN** state has `{"state": "waiting_for_title", ...}`
- **THEN** `get_current_state(user_id)` SHALL return `"waiting_for_title"`
- **WHEN** state is empty
- **THEN** `get_current_state(user_id)` SHALL return `None`

#### Scenario: new_state creates standard structure
- **WHEN** `new_state("/add", "start", {"key": "val"})` is called
- **THEN** it SHALL return `{"command": "/add", "state": "start", "data": {"key": "val"}}`

### Requirement: BotContext SHALL provide state methods
`BotContext` SHALL have `get_state()`, `set_state(state)`, `delete_state()`, `is_active()` methods and a `command_state` property that delegate to an `ActiveStateStorage` instance.

#### Scenario: BotContext delegates get_state
- **WHEN** `context.get_state()` is called
- **THEN** it SHALL return `ActiveStateStorage.get(context.user_id)`

#### Scenario: BotContext delegates set_state
- **WHEN** `context.set_state({"command": "/add", "state": "start", "data": {}})` is called
- **THEN** `ActiveStateStorage.save(context.user_id, ...)` SHALL be called with the same dict

#### Scenario: BotContext delegates delete_state
- **WHEN** `context.delete_state()` is called
- **THEN** `ActiveStateStorage.delete(context.user_id)` SHALL be called

#### Scenario: BotContext delegates is_active
- **WHEN** `context.is_active()` is called
- **THEN** it SHALL return `ActiveStateStorage.is_active(context.user_id)`

#### Scenario: BotContext exposes command_state
- **WHEN** `context.command_state` is accessed
- **THEN** it SHALL return `ActiveStateStorage.get_command(context.user_id)`

### Requirement: All handlers SHALL use BotContext state methods
All direct references to the global `active_states` dict SHALL be replaced with calls to `BotContext` state methods (`get_state`, `set_state`, `delete_state`, `is_active`, `command_state`).

#### Scenario: add.py uses context state
- **WHEN** user starts `/add` command
- **THEN** `context.set_state(...)` SHALL be used instead of `active_states[user_id] = ...`
- **WHEN** step handler processes input
- **THEN** `context.get_state()` SHALL be used instead of `active_states[user_id]`

#### Scenario: edit.py uses context state
- **WHEN** user completes or cancels edit
- **THEN** `context.delete_state()` SHALL be used instead of `del active_states[user_id]`

#### Scenario: details.py uses context state
- **WHEN** step handler checks if user is in active state
- **THEN** `context.is_active()` SHALL be used instead of `user_id in active_states`

#### Scenario: list.py uses context state
- **WHEN** handler wrapper dispatches to entry vs step
- **THEN** `context.command_state` SHALL be used instead of `active_states[user_id].get("command")`

#### Scenario: cancel.py uses context state
- **WHEN** `/cancel` is triggered
- **THEN** `if context.is_active(): context.delete_state()` SHALL be used instead of `if user_id in active_states: del active_states[user_id]`

#### Scenario: bot.py uses context state
- **WHEN** fallback routing checks for active state
- **THEN** `context.is_active()` SHALL be used instead of `context.user_id in active_states`

### Requirement: In-memory active_states SHALL be removed
The global `active_states` dict in `vk_bot/states.py` SHALL be removed, along with the file itself if it contains nothing else.

#### Scenario: active_states not importable
- **WHEN** any module tries `from vk_bot.states import active_states`
- **THEN** the import SHALL fail with `ImportError`
