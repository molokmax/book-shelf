## 1. Перенос UserStateRepository в core

- [x] 1.1 Добавить `delete_state` метод в `UserStateRepository` в `src/vk_bot/repository/user_state.py`
- [x] 1.2 Перенести класс `UserStateRepository` в `src/core/repository.py`, приведя к единому DI-стилю (принимать опциональный `db`)
- [x] 1.3 Удалить `src/vk_bot/repository/user_state.py`
- [x] 1.4 Обновить все импорты `UserStateRepository`

## 2. ActiveStateStorage

- [x] 2.1 Создать класс `ActiveStateStorage` в `src/core/storage.py` с обёрткой над `UserStateRepository`
- [x] 2.2 Реализовать методы: `get`, `save`, `delete`, `is_active`, `get_command`, `get_current_state`, `new_state`

## 3. Интеграция с BotContext

- [x] 3.1 Добавить `_storage` в `__slots__` `BotContext` и принять `storage` в конструкторе
- [x] 3.2 Добавить методы `get_state()`, `set_state()`, `delete_state()`, `is_active()` и свойство `command_state`
- [x] 3.3 В `bot.py` создать `ActiveStateStorage` и передавать его в `BotContext` при каждом событии
- [x] 3.4 Убрать импорт `active_states` из `bot.py`, заменить fallback-проверку на `context.is_active()`

## 4. Замена active_states в хендлерах

- [x] 4.1 `src/vk_bot/handlers/add.py` — заменить `active_states` на `context.*` методы
- [x] 4.2 `src/vk_bot/handlers/edit.py` — заменить `active_states` на `context.*` методы
- [x] 4.3 `src/vk_bot/handlers/details.py` — заменить `active_states` на `context.*` методы
- [x] 4.4 `src/vk_bot/handlers/list.py` — заменить `active_states` на `context.*` методы
- [x] 4.5 `src/vk_bot/handlers/cancel.py` — заменить проверку `active_states` на `context.is_active()`
- [x] 4.6 `src/vk_bot/handlers/add_handler.py` — заменить проверку `active_states` на `context.is_active() / context.command_state`
- [x] 4.7 `src/vk_bot/handlers/edit_handler.py` — то же
- [x] 4.8 `src/vk_bot/handlers/details_handler.py` — то же
- [x] 4.9 `src/vk_bot/handlers/list_handler.py` — то же

## 5. Удаление in-memory стейта

- [x] 5.1 Удалить `src/vk_bot/states.py`
- [x] 5.2 Убрать все импорты `from vk_bot.states import active_states`

## 6. Обновление тестов

- [x] 6.1 `tests/test_handler_base.py` — заменить `active_states.clear()` на мок `ActiveStateStorage`
- [x] 6.2 `tests/handlers/test_details.py`, `test_details_filter.py`, `test_details_same_day.py` — заменить стейт на моки
- [x] 6.3 `tests/handlers/test_edit_handler.py` — заменить `active_states.clear()`
- [x] 6.4 `tests/handlers/test_list.py` — заменить проверки `active_states`
- [x] 6.5 Убедиться, что `pytest` проходит без ошибок
