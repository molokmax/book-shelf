## 1. Core Implementation

- [x] 1.1 Создать `HelpHandler` в `src/vk_bot/handlers/help_handler.py` как наследника `AbstractCommandHandler`, перенеся в `handle` всё содержимое `handle_help_command` из `help.py`
- [x] 1.2 Зарегистрировать `HelpHandler()` в `CommandRouter` внутри `VkBookShelfBot.__init__`
- [x] 1.3 Удалить импорт `from vk_bot.handlers.help import handle_help_command` из `bot.py`
- [x] 1.4 Удалить блок `elif command == \"/help\": handle_help_command(context)` из `handle_event` в `bot.py`
- [x] 1.5 Удалить старый файл `src/vk_bot/handlers/help.py`

## 2. Tests

- [x] 2.1 Обновить импорты в тестах, если они ссылаются на `vk_bot.handlers.help`
- [x] 2.2 Запустить тесты (`pytest`) и убедиться, что всё проходит
