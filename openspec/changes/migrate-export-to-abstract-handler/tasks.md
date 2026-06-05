## 1. Core Implementation

- [x] 1.1 Создать `src/vk_bot/handlers/export_handler.py` — класс `ExportHandler(AbstractCommandHandler)` с `priority = 10`, `commands = ["/export", "export"]`. Перенести всю реализацию из `export.py` (логика с `BookService`, `export_to_csv`, загрузка документа) в метод `handle`
- [x] 1.2 Удалить `src/vk_bot/handlers/export.py`
- [x] 1.3 Зарегистрировать `ExportHandler()` в `CommandRouter` внутри `bot.py`, удалить `elif command == "/export"` и импорт `handle_export_command` из legacy-цепи

## 2. Tests

- [x] 2.1 Обновить `tests/handlers/test_export.py` — заменить патчи `vk_bot.handlers.export.*` на `vk_bot.handlers.export_handler.*` и импорт на `ExportHandler.handle`
- [x] 2.2 Запустить `pytest -x` и убедиться, что все тесты проходят
