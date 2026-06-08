## Context

Сейчас обработчик команды `/add` разделён на два файла:

- `add.py` — содержит `handle_add_command` (входная точка), `handle_add_command_step` (диспетчеризация по стейтам), функции-клавиатуры
- `add_handler.py` — класс `AddHandler(AbstractCommandHandler)` с методом `handle()`, который делегирует вызовы в `add.py`

Стейт-машина насчитывает 9 состояний: `choose_method`, `waiting_for_title`, `waiting_for_author`, `waiting_for_pages`, `waiting_for_link`, `waiting_for_tags`, `waiting_for_litres_url`, `waiting_for_litres_confirm`, `waiting_for_litres_tags`.

## Goals / Non-Goals

**Goals:**
- Перенести всю логику из `add.py` в `add_handler.py`
- Каждый шаг стейт-машины — отдельный приватный метод класса `AddHandler`
- Метод `handle()` диспетчеризует на `_handle_start` (новая команда) или `_handle_step` (продолжение)
- `_handle_step` читает `state` из контекста и вызывает соответствующий метод через словарь-диспетчер
- Удалить `add.py` без потери функциональности

**Non-Goals:**
- Изменение логики обработки команды `/add`
- Изменение интерфейса `AbstractCommandHandler` или `CommandRouter`
- Изменение схемы данных или бизнес-логики в `core/`

## Decisions

1. **Словарь-диспетчер вместо цепочки if/elif**  
   `_handle_step` использует `{state: method}` словарь для вызова нужного метода по `state`. Это делает добавление новых состояний тривиальным и убирает длинную цепочку условий.

2. **Методы клавиатур — @staticmethod на уровне класса**  
   Функции-клавиатуры (`create_book_added_keyboard` и др.) не используют `self`, поэтому оформлены как статические методы класса `AddHandler`. Это сохраняет их рядом с логикой, которую они обслуживают, и не требует `self`.

3. **Импорты — напрямую из модулей вместо реэкспорта через `add.py`**  
   После удаления `add.py` все импорты (`BookService`, `LitresParserError`, `is_litres_url`, `parse_litres_book`, `get_or_create_user`, `helpers`, `cancel_keyboard`, `main_keyboard`) переносятся непосредственно в `add_handler.py`.

4. **Метод handle() остаётся точкой входа**  
   `AddHandler.handle()` проверяет `context.is_active()`, чтобы решить, вызывать `_handle_start` или `_handle_step`. Это сохраняет контракт с `CommandRouter`.

## Risks / Trade-offs

- [Размер файла] `add_handler.py` станет заметно больше. Это приемлемый компромисс: один файл вместо двух, логика команды собрана в одном месте.
- [Регрессия] При рефакторинге легко пропустить импорт или сломать стейт-машину. → Покрытие тестами: все состояния должны быть проверены.
- [Тесты] Существующий тест мокает `handle_add_command` как функцию. После рефакторинга потребуется мокать метод экземпляра.
