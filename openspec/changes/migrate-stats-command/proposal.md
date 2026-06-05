## Why

Команда `/stats` — единственная команда бота, которая всё ещё реализована как обычная функция и обрабатывается через fallback-цепочку в `bot.py`, минуя `CommandRouter`. Все остальные команды уже мигрированы на `AbstractCommandHandler`. Это приводит к неоднородности кодовой базы и усложняет поддержку.

## What Changes

- Создание класса `StatsHandler` — наследника `AbstractCommandHandler` — с полной реализацией команды `/stats`
- Регистрация `StatsHandler` в `CommandRouter` через `bot.py`
- Удаление старого файла `src/vk_bot/handlers/stats.py`
- Удаление fallback-ветки для `/stats` в `bot.py`

## Capabilities

### New Capabilities
- *(нет — все возможности уже существуют)*

### Modified Capabilities
- *(нет — поведение команды `/stats` с точки зрения пользователя не меняется)*

## Impact

- `src/vk_bot/handlers/stats.py` — удаляется (весь код переносится в `stats_handler.py`)
- `src/vk_bot/handlers/stats_handler.py` — создаётся
- `src/vk_bot/bot.py` — регистрация нового хендлера и удаление fallback-ветки
- `src/vk_bot/command_router.py` — не требуется изменений (роутер уже поддерживает любые `AbstractCommandHandler`)
