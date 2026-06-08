## Why

Реализация обработчика команды `/edit` размазана между двумя файлами (`edit.py` с бизнес-логикой и `edit_handler.py` с классом-обёрткой), а шаги обработки запихнуты в одну гигантскую функцию `handle_edit_command_step` с лесенкой `if/elif`. Это затрудняет поддержку и чтение кода. Другие обработчики (например, `DetailsHandler`) уже приведены к единому стилю — вся логика в одном файле, каждый шаг в отдельном методе. Пора привести `/edit` к тому же стандарту.

## What Changes

- Вся логика из `edit.py` переносится в `edit_handler.py`
- `EditHandler.handle()` диспетчеризует вызовы по значению `state` в активном стейте
- Каждый шаг обработки (`choose_filter`, `selecting_book`, `selecting_action`, `editing_title`, `editing_author`, `editing_pages`, `editing_link`, `editing_tags`, `selecting_status_filter`, `selecting_tag_filter`, `selecting_status`, `waiting_for_progress_input`) выносится в отдельный приватный метод класса
- Файл `edit.py` удаляется
- Клавиатурные функции (`create_book_keyboard`, `create_status_keyboard`, `create_edit_keyboard`) остаются в `edit_handler.py` как статические/классовые методы или приватные функции модуля

## Capabilities

### New Capabilities
<!-- Это рефакторинг без изменения функциональности — новые spec не нужны. -->

### Modified Capabilities
<!-- Поведение команд не меняется, только внутренняя структура. Изменений в spec нет. -->

## Impact

- `src/vk_bot/handlers/edit.py` — будет удалён
- `src/vk_bot/handlers/edit_handler.py` — полностью переписан
- Импорт `edit_handler.py` в `bot.py` остаётся без изменений (класс `EditHandler` остаётся)
