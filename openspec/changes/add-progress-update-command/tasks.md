## 1. Shared Components

- [x] 1.1 Добавить `format_invalid_input(hint)` в `src/utils/helpers.py`.
- [x] 1.2 Создать пакет `src/vk_bot/flows/` и `BookSelectionFlow` для состояний `choose_filter`, `selecting_status_filter`, `selecting_tag_filter`, `selecting_book`.
- [x] 1.3 Создать `ProgressUpdateFlow` для запроса, проверки, подтверждения и применения прогресса.
- [x] 1.4 Добавить `TODO(#42)` о миграции `list`, `details` и `edit` на общий выбор книги.

## 2. Progress Handler

- [x] 2.1 Создать `src/vk_bot/handlers/progress.py` с командами `/progress`, `progress`, `прогресс`.
- [x] 2.2 Реализовать вход, список книг со статусом `reading` и пустое состояние.
- [x] 2.3 Реализовать кнопку `Другие` и переход в `BookSelectionFlow`.
- [x] 2.4 Реализовать выбор книги и переход к вводу прогресса без промежуточного меню.
- [x] 2.5 Реализовать отказ от обработки `/progress` при активном состоянии другой команды.
- [x] 2.6 Зарегистрировать `ProgressHandler` в `src/vk_bot/bot.py`.

## 3. Edit Cleanup and Legacy

- [x] 3.1 Убрать кнопку `Прогресс` из клавиатуры действий `/edit`.
- [x] 3.2 Убрать ветку `прогресс` из `_handle_selecting_action` и добавить общий fallback `⚠️ Выбери действие`.
- [x] 3.3 Перевести legacy-состояния `waiting_for_progress_input` и `waiting_for_progress_confirm` на `ProgressUpdateFlow`.
- [x] 3.4 Добавить `TODO(#69)` на удаление legacy-делегирования после переходного периода.

## 4. Menu and Documentation

- [x] 4.1 Обновить `main_keyboard` до раскладки `/progress`, `/edit`, `/add`, `/list`, `/details`, `/export`, `/stats`, `/help`.
- [x] 4.2 Добавить `/progress` в тексты `/start` и `/help`.
- [x] 4.3 Обновить README описанием новой команды.

## 5. Tests

- [x] 5.1 Добавить тесты входа в `/progress`, списка `reading`, пустого списка и кнопки `Другие`.
- [x] 5.2 Добавить тесты стандартного выбора книги по статусу, тегу и всем книгам.
- [x] 5.3 Перенести и адаптировать тесты прогресса из `test_edit_handler.py`.
- [x] 5.4 Добавить тесты стандартного сообщения о неверном вводе и сохранения состояния.
- [x] 5.5 Добавить тест отказа `ProgressHandler` при активном состоянии другой команды.
- [x] 5.6 Добавить тест legacy-состояний `/edit` через `ProgressUpdateFlow`.
- [x] 5.7 Добавить тест fallback в меню действий `/edit`.

## 6. Verification

- [x] 6.1 Запустить `isort .`.
- [x] 6.2 Запустить `black .`.
- [x] 6.3 Запустить `flake8 src/`.
- [x] 6.4 Запустить `pytest`.
- [x] 6.5 Проверить `openspec status --change add-progress-update-command`.
