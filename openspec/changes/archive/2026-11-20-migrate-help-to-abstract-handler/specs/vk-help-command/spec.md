## ADDED Requirements

### Requirement: Help command handled via AbstractCommandHandler
Система SHALL обрабатывать команду `/help` через `HelpHandler`, наследующий `AbstractCommandHandler` и зарегистрированный в `CommandRouter`.

#### Scenario: HelpHandler registered in CommandRouter
- **WHEN** бот запускается и `VkBookShelfBot.__init__` выполняется
- **THEN** `HelpHandler()` зарегистрирован в `CommandRouter` через `register_handler`

#### Scenario: HelpHandler routes /help and help
- **WHEN** пользователь отправляет `/help` или `help`
- **THEN** `HelpHandler.can_handle` возвращает `True` для этих команд

#### Scenario: HelpHandler sends help text
- **WHEN** `HelpHandler.handle` вызывается с валидным `BotContext`
- **THEN** отправляется сообщение с текстом справки и основной клавиатурой

#### Scenario: Old help.py implementation inlined in HelpHandler
- **WHEN** `help.py` прочитан
- **THEN** его содержимое целиком перенесено в `HelpHandler.handle`, а сам `help.py` удалён

### Requirement: Legacy help code removed
Система SHALL не содержать старой реализации команды `/help` в `bot.py`.

#### Scenario: No legacy import in bot.py
- **WHEN** `bot.py` импортируется
- **THEN** в нём нет импорта `from vk_bot.handlers.help import handle_help_command`

#### Scenario: No legacy if/elif for /help
- **WHEN** `handle_event` обрабатывает команду `/help`
- **THEN** команда не маршрутизируется через `elif command == "/help"` в `handle_event`
