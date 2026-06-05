## Why

Команда `/start` — единственная команда бота, которая обрабатывается вне системы роутинга (через ручной `if-elif` в `bot.py`). Это нарушает единообразие архитектуры и затрудняет поддержку. Необходимо привести `/start` к общему паттерну `AbstractCommandHandler`, чтобы все команды обрабатывались единообразно через `CommandRouter`.

## What Changes

- Создать `StartHandler(AbstractCommandHandler)` с наивысшим приоритетом (выше всех остальных)
- Перенести логику из `handle_start_command` в `StartHandler.handle()`
- Зарегистрировать `StartHandler` в `CommandRouter` в `bot.py`
- Удалить ручную обработку `/start` из `handle_event()` в `bot.py`
- Удалить старый файл `src/vk_bot/handlers/start.py` (логика переносится в новый `start_handler.py`)

## Capabilities

### New Capabilities
- `start-command`: Обработка команды `/start` через `AbstractCommandHandler` с наивысшим приоритетом

### Modified Capabilities
*(нет изменений существующих spec-файлов)*

## Impact

- **Код**: `src/vk_bot/handlers/start.py` → удаляется; создаётся `src/vk_bot/handlers/start_handler.py`; изменяется `src/vk_bot/bot.py`
- **Зависимости**: нет новых зависимостей
- **Логика**: поведение команды `/start` не меняется, только способ маршрутизации
