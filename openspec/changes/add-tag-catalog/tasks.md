## 1. Схема и миграция

- [x] 1.1 Таблицы `tags` и `book_tags` в `_create_tables` (`src/core/database.py`) со схемой из design.md (UNIQUE, FK с ON DELETE CASCADE)
- [x] 1.2 `migrate_books_tags` в `src/core/migrations.py`: парсинг `books.tags` (`ast.literal_eval`, fallback `json.loads`, иначе пусто с warning), casefold-дедуп по пользователю, `INSERT OR IGNORE` тегов, пересборка `book_tags`, `DROP COLUMN tags` (идемпотентно)
- [x] 1.3 Убрать `tags` из `CREATE TABLE books` и `_book_column_list`
- [x] 1.4 Тесты миграции: перенос значений, идемпотентность повторного запуска, casefold-дедуп («Tech»/«tech»), повреждённые значения, NULL и пустые строки, удаление колонки

## 2. Слой данных

- [x] 2.1 `Database.add_or_update_book`: ensure тегов справочника + DELETE/INSERT `book_tags` одним курсором
- [x] 2.2 Гидратация тегов в `get_book_by_id`, `get_all_books`, `get_books_by_user_id`, `get_books_by_status` (JOIN, сортировка casefold)
- [x] 2.3 `TagRepository` в `src/core/repository.py`: `get_user_tags(user_id)` (справочник), `get_used_tags(user_id)` (привязанные к книгам)
- [x] 2.4 `TagService` в `src/core/services.py`
- [x] 2.5 `BookService.get_all_tags` переключить на `get_used_tags`, сигнатура не меняется
- [x] 2.6 Тесты: запись и чтение тегов, casefold-дедуп, справочник против используемых, каскад при удалении книги, атомарность записи

## 3. Клавиатура шага тегов

- [x] 3.1 `tag_editing_keyboard(tags, selected, page, owner_command)` в `src/vk_bot/keyboards.py`: 2 тега в ряд, 16 на страницу, primary/secondary, ряд «Готово» (positive) + «Отмена» (negative, payload `/cancel`), ряд пагинации с payload
- [x] 3.2 Тесты клавиатуры: раскладка, подсветка, пагинация, лимит кнопок

## 4. TagEditingFlow

- [x] 4.1 `src/vk_bot/flows/tag_editing.py`: `start(context, state_info, preselected)`, `handle(context, state_info)`: payload toggle/done/prev_page/next_page, текстовый ввод («готово», список через запятую, мусор)
- [x] 4.2 Валидация toggle по справочнику пользователя, casefold-резолв ввода к каноническим именам
- [x] 4.3 Тесты flow: вход, toggle туда и обратно, ввод списком, ввод «готово», пустой ввод, пагинация, подменённый payload, вызов `on_done` с итоговой выборкой

## 5. Интеграция хендлеров

- [x] 5.1 `add.py`: `waiting_for_link` и `waiting_for_litres_confirm` ведут в `selecting_tags` (origin manual/litres); `on_done` создаёт книгу; финальное сообщение перечисляет теги
- [x] 5.2 `edit.py`: `editing_link` ведёт в `selecting_tags` с предвыбором текущих тегов; `on_done` применяет накопленные поля + теги; сообщение перечисляет теги
- [x] 5.3 Тесты хендлеров: оба пути `/add`, `/edit`, «Готово» с пустой выборкой (add без тегов, edit снимает все), гард чужого сценария, отмена

## 6. Терминология и документация

- [x] 6.1 `CONTEXT.md`: термины «Тег», «Набор тегов пользователя»
- [x] 6.2 Унификация «тег» в сообщениях бота (`edit.py` 495, 499; `services.py` 162) и всех новых текстах
- [x] 6.3 `README.md`: справочник тегов, интерактивный выбор, раздел об обновлении (бэкап `data/database.db` перед первым запуском)

## 7. Проверка

- [x] 7.1 `isort .`, `black .`, `flake8 src/`, `pytest`: всё зелёное
