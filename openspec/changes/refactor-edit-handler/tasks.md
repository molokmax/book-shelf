## 1. Подготовка

- [x] 1.1 Прочитать `edit.py` и идентифицировать все состояния и их обработку
- [x] 1.2 Прочитать `details_handler.py` как референсный паттерн

## 2. Реализация в edit_handler.py

- [x] 2.1 Добавить все необходимые импорты из `edit.py` в `edit_handler.py`
- [x] 2.2 Создать метод `_handle_entry` — инициализация состояния `/edit`
- [x] 2.3 Создать метод `_handle_choose_filter` — выбор фильтра (по статусу / по тегам / все)
- [x] 2.4 Создать метод `_handle_selecting_book` — выбор книги по номеру
- [x] 2.5 Создать метод `_handle_selecting_action` — выбор действия над книгой
- [x] 2.6 Создать методы редактирования: `_handle_editing_title`, `_handle_editing_author`, `_handle_editing_pages`, `_handle_editing_link`, `_handle_editing_tags`
- [x] 2.7 Создать метод `_handle_selecting_status_filter` — выбор статуса для фильтрации
- [x] 2.8 Создать метод `_handle_selecting_tag_filter` — выбор тега для фильтрации
- [x] 2.9 Создать метод `_handle_selecting_status` — смена статуса книги
- [x] 2.10 Создать метод `_handle_waiting_for_progress_input` — обновление прогресса чтения
- [x] 2.11 Обновить `handle()` для диспетчеризации по `state_info["state"]`
- [x] 2.12 Перенести клавиатурные функции как статические методы класса

## 3. Завершение

- [x] 3.1 Удалить файл `src/vk_bot/handlers/edit.py`
- [x] 3.2 Проверить импорт `EditHandler` в `bot.py` (он уже есть из edit_handler)
- [x] 3.3 Запустить тесты: `pytest -x` (73 passed)
- [x] 3.4 Запустить линтер: `flake8 src/` (чисто)
