## 1. Перенести реализацию в list_handler.py

- [x] 1.1 Добавить в `ListHandler` метод `_handle_entry` — установка начального стейта и отправка клавиатуры фильтров (из `handle_list_command`)
- [x] 1.2 Добавить метод `_handle_choose_filter` — обработка выбора фильтра (из `handle_list_command_step` / state == "choose_filter")
- [x] 1.3 Добавить метод `_handle_choose_status` — обработка выбора статуса (из `handle_list_command_step` / state == "choose_status")
- [x] 1.4 Добавить метод `_handle_choose_tag` — обработка выбора тега (из `handle_list_command_step` / state == "choose_tag")
- [x] 1.5 Добавить метод `_finish` — завершение команды, очистка стейта
- [x] 1.6 Переписать `ListHandler.handle()` — диспетчеризация по `state` через `getattr`

## 2. Удалить list.py и обновить тесты

- [x] 2.1 Удалить `src/vk_bot/handlers/list.py`
- [x] 2.2 Обновить `tests/handlers/test_list.py` — импортировать `ListHandler` вместо `vk_bot.handlers.list`
- [x] 2.3 Запустить тесты: `pytest`