## 1. Создание StatsHandler

- [x] 1.1 Создать файл `src/vk_bot/handlers/stats_handler.py` с классом `StatsHandler`, наследующим `AbstractCommandHandler`
- [x] 1.2 Перенести логику из `handle_stats_command` в метод `handle` класса `StatsHandler`
- [x] 1.3 Добавить импорты: `AbstractCommandHandler`, `BotContext`, `BookService`, `get_or_create_user`, `main_keyboard`, `get_random_id`

## 2. Регистрация в боте

- [x] 2.1 Импортировать `StatsHandler` в `src/vk_bot/bot.py`
- [x] 2.2 Зарегистрировать `StatsHandler()` в `CommandRouter` через `self.router.register_handler(StatsHandler())`

## 3. Очистка старой реализации

- [x] 3.1 Удалить `from vk_bot.handlers.stats import handle_stats_command` из `bot.py`
- [x] 3.2 Удалить fallback-ветку `elif command == "/stats": handle_stats_command(context)` из `bot.py`
- [x] 3.3 Удалить файл `src/vk_bot/handlers/stats.py`
