## 1. Создание обработчика StartHandler

- [x] 1.1 Создать файл `src/vk_bot/handlers/start_handler.py` с классом `StartHandler(AbstractCommandHandler)`, priority=1000, commands=["/start", "start", "начать"]
- [x] 1.2 Перенести логику из `handle_start_command` (из `start.py`) в `StartHandler.handle()`

## 2. Регистрация и очистка

- [x] 2.1 Зарегистрировать `StartHandler()` в `VkBookShelfBot.__init__()` через `router.register_handler()`
- [x] 2.2 Удалить блок `if command == "/start" or command == "начать": handle_start_command(context)` из `VkBookShelfBot.handle_event()`
- [x] 2.3 Удалить файл `src/vk_bot/handlers/start.py`

## 3. Верификация

- [x] 3.1 Запустить линтер: `flake8 src/`
- [x] 3.2 Запустить тесты: `pytest`
- [x] 3.3 Убедиться, что команда `/start` работает через роутер (без ручной обработки)
