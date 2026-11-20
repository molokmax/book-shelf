## Context

Сейчас обработчик `/edit` разбит на два файла:
- `edit.py` — две свободные функции `handle_edit_command()` и `handle_edit_command_step()` с гигантской лесенкой `if/elif` по состояниям
- `edit_handler.py` — класс `EditHandler`, который делегирует вызовы этим функциям

Другие обработчики (`DetailsHandler`, `AddHandler`) уже следуют единому паттерну: вся логика в одном файле, приватные методы на каждое состояние, диспетчеризация через `if/elif` по `state`.

## Goals / Non-Goals

**Goals:**
- Перенести всю логику из `edit.py` в `edit_handler.py`
- Разбить `handle_edit_command_step()` на отдельные приватные методы по состояниям
- Диспетчеризация по `state` в `EditHandler.handle()`
- Удалить `edit.py`

**Non-Goals:**
- Изменение поведения команд или сообщений пользователю
- Изменение клавиатур или форматов вывода
- Рефакторинг `AddHandler` или других обработчиков

## Decisions

1. **Паттерн диспетчеризации** — копируем подход `DetailsHandler`:
   - `handle()` проверяет `context.is_active()` и `state_info["state"]`
   - Каждый `state` → отдельный `_handle_<state>()` метод
   - Клавиатурные функции остаются как `@staticmethod` внутри класса
2. **Именование методов** — `<состояние>` в snake_case, например:
   - `_handle_choose_filter`
   - `_handle_selecting_book`
   - `_handle_selecting_action`
   - `_handle_editing_title`, `_handle_editing_author`, и т.д.
   - `_handle_selecting_status_filter`
   - `_handle_selecting_tag_filter`
   - `_handle_selecting_status`
   - `_handle_waiting_for_progress_input`
3. **Импорты** — все импорты из `edit.py` переносятся в `edit_handler.py`
4. **Удаление `edit.py`** — после переноса файл удаляется, корректируется импорт в `__init__.py` если необходимо

## Risks / Trade-offs

- **Риск**: Пропустить какое-то состояние при переносе → **Митигация**: покрыть все 12 состояний, свериться с исходным кодом
- **Риск**: Случайно изменить логику при разбиении → **Митигация**: сохранить точную последовательность вызовов API и сообщений
