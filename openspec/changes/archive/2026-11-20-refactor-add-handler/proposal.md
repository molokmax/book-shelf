## Why

Сейчас логика команды `/add` разделена между `add.py` (весь стейт-машин и утилиты) и `add_handler.py` (тонкая обёртка-наследник `AbstractCommandHandler`). Это приводит к дублированию контекста и усложняет поддержку. Каждый шаг обработки сообщения должен быть отдельным методом внутри `AddHandler`, а `add.py` нужно удалить.

## What Changes

- Перенести всю логику из `add.py` в `add_handler.py`, включая:
  - `handle_add_command` → метод `_handle_start` класса `AddHandler`
  - `handle_add_command_step` → метод `_handle_step` класса `AddHandler`, который диспетчеризует по значению `state` на отдельные приватные методы
  - Каждый `if state == ...` блок становится отдельным методом (например, `_handle_choose_method`, `_handle_waiting_for_title`, и т.д.)
  - Функции-клавиатуры (`create_book_added_keyboard`, `create_add_method_keyboard`, `create_link_keyboard`, `create_confirm_litres_keyboard`) перенести как методы класса или модульные функции в `add_handler.py`
- Удалить `add.py`
- Обновить импорты в `add_handler.py` (убрать импорты из `add.py`, добавить недостающие импорты напрямую)

## Capabilities

### New Capabilities
- `add-handler-refactoring`: Перенос реализации обработчика `/add` в `add_handler.py` с выделением каждого шага в отдельный метод и диспетчеризацией по `state`

### Modified Capabilities
- *(none — поведение команды не меняется)*

## Impact

- `src/vk_bot/handlers/add.py` — будет удалён
- `src/vk_bot/handlers/add_handler.py` — значительно расширится (весь код из `add.py`)
- `tests/test_handler_base.py` — может потребовать обновления моков (заменить `handle_add_command` на метод экземпляра)
