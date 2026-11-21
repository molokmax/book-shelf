## 1. Создание CancelHandler

- [x] 1.1 Создать `src/vk_bot/handlers/cancel_handler.py` с классом `CancelHandler(AbstractCommandHandler)`, priority=100, commands=["/cancel", "cancel", "отмена"]
- [x] 1.2 Перенести логику из `handle_cancel_command` в `CancelHandler.handle()`

## 2. Регистрация и очистка

- [x] 2.1 Зарегистрировать `CancelHandler()` в `CommandRouter` в `bot.py`
- [x] 2.2 Удалить `if command == "/cancel"` и `elif command == "отмена"` из `bot.py:126-127`
- [x] 2.3 Удалить import `handle_cancel_command` из `bot.py`
- [x] 2.4 Удалить файл `src/vk_bot/handlers/cancel.py`

## 3. Проверка

- [x] 3.1 Запустить тесты: `pytest`
