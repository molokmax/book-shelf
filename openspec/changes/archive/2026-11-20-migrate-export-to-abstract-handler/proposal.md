## Why

Команда `/export` — единственная активная команда бота, которая ещё не использует `AbstractCommandHandler`. После миграции всех остальных команд (add, edit, list, details) export остаётся в старом `if/elif`-роутинге, что нарушает единообразие архитектуры. Необходимо привести её к общему паттерну для централизованной обработки и устранения legacy-пути.

## What Changes

- Создать `ExportHandler` как наследника `AbstractCommandHandler` с приоритетом 10 и перенести в него всю реализацию из `export.py`
- Удалить старый файл `src/vk_bot/handlers/export.py`
- Удалить обработку `/export` из `if/elif`-блока в `bot.py`
- Удалить импорт `handle_export_command` из `bot.py`
- Обновить тесты: заменить патчи `vk_bot.handlers.export.*` на `vk_bot.handlers.export_handler.*`

## Capabilities

### New Capabilities
<!-- Нет новых возможностей — только миграция существующей команды на новый роутинг -->

### Modified Capabilities
<!-- Поведение команды не меняется, спецификация vk-export-csv остаётся без изменений -->

## Impact

- `src/vk_bot/handlers/export_handler.py` — новый файл с полной реализацией
- `src/vk_bot/handlers/export.py` — удаляется
- `src/vk_bot/bot.py` — регистрация `ExportHandler()`, удаление `elif command == "/export"` и импорта
- `tests/handlers/test_export.py` — обновление путей патчей
- `src/core/`, `src/utils/export.py` — без изменений
