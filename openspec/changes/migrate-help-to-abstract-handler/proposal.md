## Why

Команда `/help` — единственная команда из основного наряду с `/start`, `/cancel`, `/stats`, которая всё ещё обрабатывается через старый `if/elif` маршрут в `bot.py`, а не через `CommandRouter` и `AbstractCommandHandler`. Это нарушает единообразие архитектуры и мешает полному переходу на приоритетную маршрутизацию.

## What Changes

- Создание `HelpHandler` — наследника `AbstractCommandHandler` — в новом файле `src/vk_bot/handlers/help_handler.py` с переносом всего содержимого `handle_help_command` из `help.py` в `HelpHandler.handle`
- Регистрация `HelpHandler()` в `CommandRouter` внутри `VkBookShelfBot.__init__`
- Удаление импорта `handle_help_command` из `bot.py`
- Удаление блока `elif command == "/help": handle_help_command(context)` из `bot.py`
- Удаление старого файла `src/vk_bot/handlers/help.py`

## Capabilities

### New Capabilities
- `vk-help-command`: Миграция команды `/help` на использование `AbstractCommandHandler` и `CommandRouter`

### Modified Capabilities
*(нет изменений требований существующих specs)*

## Impact

- `src/vk_bot/bot.py` — удаление legacy импорта и `elif`-ветки
- `src/vk_bot/handlers/help.py` — полное удаление файла
- Создание `src/vk_bot/handlers/help_handler.py`
- Тесты: обновление путей при необходимости
