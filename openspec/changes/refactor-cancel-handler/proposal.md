## Why

Обработчик команды `/cancel` остался единственным, кто не использует базовый класс `AbstractCommandHandler`. Это нарушает единообразие архитектуры: команда обрабатывается через прямой `if` в `bot.py`, минуя `CommandRouter`, лишаясь преимуществ приоритетной маршрутизации и централизованной обработки ошибок.

## What Changes

- Создать `CancelHandler` — класс-наследник `AbstractCommandHandler` с наивысшим приоритетом
- Перенести логику из `handle_cancel_command` в `CancelHandler.handle()`
- Зарегистрировать `CancelHandler` в `CommandRouter` в `bot.py`
- Удалить старый файл `cancel.py` и вызов `handle_cancel_command` из `bot.py`

## Capabilities

### New Capabilities

Нет новых пользовательских возможностей — это внутренний рефакторинг.

### Modified Capabilities

Нет изменений в спеках — поведение команды `/cancel` остаётся тем же.

## Impact

- `src/vk_bot/handlers/cancel.py` — удалить
- `src/vk_bot/handlers/cancel_handler.py` — создать
- `src/vk_bot/bot.py` — заменить прямой вызов на регистрацию в роутере, убрать import cancel
