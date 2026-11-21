## ADDED Requirements

### Requirement: BotContext construction
The system SHALL provide a `BotContext` class that encapsulates all runtime data needed by command handlers.

The constructor SHALL accept three arguments:
- `vk` — an instance of `vk_api.VkApi`
- `upload` — an instance of `vk_api.tools.VkUpload`
- `event` — an instance of `vk_api.longpoll.Event`

All arguments SHALL be stored as public read-only attributes with the same names.

#### Scenario: Context created with real VK objects
- **WHEN** `BotContext` is instantiated with a `VkApi` instance, a `VkUpload` instance, and a LongPoll `Event` instance
- **THEN** `context.vk` SHALL be the `VkApi` instance, `context.upload` SHALL be the `VkUpload` instance, and `context.event` SHALL be the `Event` instance

#### Scenario: Context created for testing
- **WHEN** `BotContext` is instantiated with mock objects for `vk`, `upload`, and `event`
- **THEN** it SHALL accept any objects — no type validation is performed at construction

---

### Requirement: Access to event data
`BotContext` SHALL provide read-only properties that delegate to the underlying `event` object:

| Property   | Delegates to `event.` |
|------------|----------------------|
| `user_id`  | `user_id`            |
| `peer_id`  | `peer_id`            |
| `text`     | `text`               |

#### Scenario: Properties return event fields
- **WHEN** `event.user_id = 123`, `event.peer_id = 456`, `event.text = "hello"`
- **THEN** `context.user_id` SHALL return `123`, `context.peer_id` SHALL return `456`, `context.text` SHALL return `"hello"`

---

### Requirement: Access to payload
`BotContext` SHALL provide a `payload` property that returns the parsed payload dictionary from the event.

If `event.payload` is `None` or empty, the property SHALL return an empty `dict`.

#### Scenario: Event has JSON payload
- **WHEN** `event.payload = '{"command":"/cancel","status":"reading"}'`
- **THEN** `context.payload` SHALL return `{"command": "/cancel", "status": "reading"}`

#### Scenario: Event has no payload
- **WHEN** `event.payload` is `None`
- **THEN** `context.payload` SHALL return `{}`

#### Scenario: Event has empty payload
- **WHEN** `event.payload = ""`
- **THEN** `context.payload` SHALL return `{}`

---

### Requirement: Command extraction
`BotContext` SHALL provide a `command` property that extracts the command.

Extraction order:
1. If `payload` contains a `"command"` key, return its value
2. Otherwise, return `text` (lowercased)

#### Scenario: Command from payload
- **WHEN** `context.payload = {"command": "/cancel"}` and `context.text = "some text"`
- **THEN** `context.command` SHALL return `"/cancel"`

#### Scenario: Command from text fallback
- **WHEN** `context.payload = {}` and `context.text = "/Add Book"`
- **THEN** `context.command` SHALL return `"/add book"`

---

### Requirement: Immutable attributes
The attributes `vk`, `upload`, and `event` SHALL NOT be reassignable after construction.

#### Scenario: Attribute reassignment raises error
- **WHEN** attempting `context.vk = new_value`
- **THEN** an `AttributeError` SHALL be raised (consistent with using `@property` without a setter, or `__slots__`, or `NamedTuple`)
