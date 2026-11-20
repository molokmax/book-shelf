## 1. Перенос статических методов-клавиатур

- [x] 1.1 Перенести `create_book_added_keyboard` как `@staticmethod` в `AddHandler`
- [x] 1.2 Перенести `create_add_method_keyboard` как `@staticmethod` в `AddHandler`
- [x] 1.3 Перенести `create_link_keyboard` как `@staticmethod` в `AddHandler`
- [x] 1.4 Перенести `create_confirm_litres_keyboard` как `@staticmethod` в `AddHandler`

## 2. Перенос входной точки /add

- [x] 2.1 Создать метод `_handle_start` в `AddHandler`, реализующий логику `handle_add_command`
- [x] 2.2 Обновить `handle()`: вызывать `_handle_start(context)` если `not context.is_active()` или `context.command_state != "/add"`

## 3. Перенос стейт-машины с выделением шагов

- [x] 3.1 Создать метод `_handle_choose_method` (обработка выбора "Ручное"/"Из LitRes")
- [x] 3.2 Создать метод `_handle_waiting_for_title`
- [x] 3.3 Создать метод `_handle_waiting_for_author`
- [x] 3.4 Создать метод `_handle_waiting_for_pages`
- [x] 3.5 Создать метод `_handle_waiting_for_link`
- [x] 3.6 Создать метод `_handle_waiting_for_tags`
- [x] 3.7 Создать метод `_handle_waiting_for_litres_url`
- [x] 3.8 Создать метод `_handle_waiting_for_litres_confirm`
- [x] 3.9 Создать метод `_handle_waiting_for_litres_tags`
- [x] 3.10 Создать метод `_handle_step` со словарём-диспетчером `{state: method}` и обработкой неизвестного state

## 4. Обновление импортов и удаление add.py

- [x] 4.1 Добавить прямые импорты в `add_handler.py` (`BookService`, `LitresParserError`, `is_litres_url`, `parse_litres_book`, `get_or_create_user`, `helpers`, `cancel_keyboard`, `main_keyboard`, `get_random_id`)
- [x] 4.2 Удалить `add.py`
- [x] 4.3 Обновить тест в `tests/test_handler_base.py`: замокать `AddHandler._handle_start` вместо `handle_add_command`

## 5. Проверка

- [x] 5.1 Запустить тесты: `pytest tests/ -x`
- [x] 5.2 Запустить линтер: `flake8 src/vk_bot/handlers/add_handler.py`
