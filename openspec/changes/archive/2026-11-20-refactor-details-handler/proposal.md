## Why

Текущая реализация команды `/details` находится в двух файлах: `details.py` (вся логика шагов) и `details_handler.py` (тонкая обёртка-прокси). Обработка каждого шага размазана по одной большой функции `handle_details_step` с цепочкой `if/elif`. Это усложняет поддержку, тестирование и расширение. **Цель** — перенести всю логику в `details_handler.py`, разделив каждый шаг состояния на отдельный метод, и сделать `details.py` удаляемым.

## What Changes

- Перенести `handle_details` и `handle_details_step` из `details.py` в `DetailsHandler` класса в `details_handler.py`
- Разбить `handle_details_step` на отдельные методы по каждому состоянию:
  - `_handle_choose_filter`
  - `_handle_selecting_status_filter`
  - `_handle_selecting_tag_filter`
  - `_handle_selecting_book`
- Метод `handle(context)` диспетчеризует вызов на основе `state` из активного стейта
- Удалить `details.py`
- Удалить импорт `details` из `details_handler.py`
- Обновить тесты, чтобы они импортировали `DetailsHandler` напрямую, а не функции из `details.py`

## Capabilities

### New Capabilities

*(нет — это внутренний рефакторинг, без изменения пользовательского API)*

### Modified Capabilities

- `book-details-view`: implementation details меняются (логика переезжает в handler), но требования spec не изменяются

## Impact

- `src/vk_bot/handlers/details.py` — удалить
- `src/vk_bot/handlers/details_handler.py` — полностью переписать: добавить приватные методы для каждого шага, переделать `handle` на диспетчеризацию по `state`
- `tests/handlers/test_details.py` — обновить импорты и вызовы под новую структуру
- `tests/handlers/test_details_filter.py` — то же
- `tests/handlers/test_details_same_day.py` — то же
