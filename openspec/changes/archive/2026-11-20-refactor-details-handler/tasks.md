## 1. Рефакторинг details_handler.py

- [x] 1.1 Перенести `handle_details` в `DetailsHandler` как метод `_handle_entry`
- [x] 1.2 Разбить `handle_details_step` на методы `_handle_choose_filter`, `_handle_selecting_status_filter`, `_handle_selecting_tag_filter`, `_handle_selecting_book`, `_handle_display_details`
- [x] 1.3 Реализовать диспетчеризацию в `handle(context)`: проверять `context.is_active()`, читать `state` из стейта и вызывать соответствующий `_handle_*` метод

## 2. Удаление details.py

- [x] 2.1 Убрать импорт `from .details import handle_details, handle_details_step` из `details_handler.py`
- [x] 2.2 Удалить файл `src/vk_bot/handlers/details.py`
- [x] 2.3 Проверить grep-ом, что `details` нигде больше не импортируется

## 3. Обновление тестов

- [x] 3.1 Обновить `tests/handlers/test_details.py`: импортировать `DetailsHandler` вместо функций из `details.py`, использовать вызов `handler.handle(context)` для тестирования
- [x] 3.2 Обновить `tests/handlers/test_details_filter.py`: аналогично
- [x] 3.3 Обновить `tests/handlers/test_details_same_day.py`: аналогично

## 4. Валидация

- [x] 4.1 Прогнать `pytest tests/handlers/test_details.py tests/handlers/test_details_filter.py tests/handlers/test_details_same_day.py`
- [x] 4.2 Прогнать `flake8 src/`
- [x] 4.3 Убедиться, что `details.py` удалён и нигде не требуется
