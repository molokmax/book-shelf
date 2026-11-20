## Context

Команда `/export` — последняя активная команда, которая не использует `AbstractCommandHandler`. Обработка вызова (`handle_export_command`) находится в `export.py`, а роутинг идёт через legacy `if/elif`-блок в `bot.py:129-130`. Остальные четыре команды (`add`, `edit`, `list`, `details`) уже мигрированы на `AbstractCommandHandler` и зарегистрированы в `CommandRouter`.

В отличие от add или edit, export — одношаговая команда без состояния: получил запрос → сгенерировал CSV → отправил файл.

## Goals / Non-Goals

**Goals:**
- Создать `ExportHandler` (наследник `AbstractCommandHandler`) с полной реализацией в `export_handler.py`
- Удалить старый файл `src/vk_bot/handlers/export.py`
- Зарегистрировать `ExportHandler` в `CommandRouter` через `bot.py`
- Удалить `elif command == "/export"` и импорт из legacy-цепи `bot.py`
- Обновить тесты: патчи `vk_bot.handlers.export.*` → `vk_bot.handlers.export_handler.*`

**Non-Goals:**
- Не менять бизнес-логику генерации CSV и загрузки в VK
- Не добавлять многошаговый сценарий (state) для export
- Не затрагивать другие команды (`/start`, `/help`, `/stats`, `/cancel`)
- Не менять тесты, если они не относятся к роутингу export

## Decisions

1. **ExportHandler без state-логики** — export одношаговый, поэтому метод `handle` просто вызывает `handle_export_command(context)` без проверки `context.is_active()`. Это проще, чем паттерн add_handler с ветвлением на step/entry.
2. **Приоритет 10** — совпадает с остальными обработчиками-наследниками (AddHandler, EditHandler, ListHandler, DetailsHandler). Порядок неважен, так как команды уникальны.
3. **Список команд `["/export", "export"]`** — аналогично другим обработчикам: поддерживается как слэш-форма, так и без.
4. **Перенос реализации в `export_handler.py`** — вся логика из `export.py` (функция `handle_export_command`) переносится в метод `handle` класса `ExportHandler`. Старый файл `export.py` удаляется.
5. **Обновление тестов** — существующие тесты патчат `vk_bot.handlers.export.*`; после переноса патчи меняются на `vk_bot.handlers.export_handler.*`.

## Risks / Trade-offs

- **Риск:** забыть удалить `elif command == "/export"` и импорт из bot.py — команда выполнится дважды или будет ошибка импорта. **Митигация:** удалить эти строки в том же коммите, где добавляется регистрация.
- **Риск:** тесты патчат старые пути `vk_bot.handlers.export.*` — после удаления `export.py` тесты упадут с `ModuleNotFoundError`. **Митигация:** обновить пути патчей в `tests/handlers/test_export.py` в том же коммите.
- **Риск:** `context.upload.document_message` и `context.api.messages.send` — `BotContext` предоставляет эти атрибуты. **Митигация:** проверить по аналогии с другими обработчиками.
