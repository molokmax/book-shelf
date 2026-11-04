## 1. Клавиатуры

- [x] 1.1 `main_keyboard()` (`src/vk_bot/keyboards.py`): ряд 1 `/progress` `/details` `/list`; ряд 2 `/add` `/help` «Ещё» с payload `{"command": "/more"}`
- [x] 1.2 `more_keyboard()` в `src/vk_bot/keyboards.py`: ряд 1 `/edit` `/export` `/goal`; ряд 2 `/stats` `/settings` «Назад» с payload `{"command": "/back"}`
- [x] 1.3 Тесты раскладок: обновить `test_main_keyboard_contains_progress_command` (`tests/handlers/test_progress_handler.py`) под новую раскладку; добавить тест `more_keyboard()` (порядок кнопок в двух рядах, payload «Назад»)

## 2. MoreHandler

- [x] 2.1 `src/vk_bot/handlers/more.py`: `MoreHandler` (priority 10, `commands = ["/more", "/back"]`) с гардом чужого сценария (`return None` при `context.is_active()` и команде стейта вне `["/more", "/back"]`)
- [x] 2.2 `/more`: экран «Ещё» (текст из design.md, п. 4) с `more_keyboard()`; состояние диалога не пишется
- [x] 2.3 `/back`: сообщение «Главное меню» с `main_keyboard()`
- [x] 2.4 Импорт и регистрация `MoreHandler` в `src/vk_bot/bot.py`
- [x] 2.5 Тесты `tests/handlers/test_more_handler.py`: `/more` открывает экран с подменю и не создаёт состояние; `/back` возвращает «Главное меню» с главной клавиатурой; гард: `/more` и `/back` при чужом активном сценарии возвращают `None`; «Отмена» работает глобально из подменю

## 3. Тексты /start и /help

- [x] 3.1 `handlers/start.py`: новый текст приветствия (черновик из design.md, п. 8)
- [x] 3.2 `handlers/help.py`: строка `* /details - Полная информация о выбранной книге`
- [x] 3.3 Обновить тесты, где захардкожены тексты `/start` и `/help` (захардкоженных текстов в тестах нет, правки не требуются)

## 4. Проверка

- [x] 4.1 Прогнать `isort .`, `black .`, `flake8 src/`, `pytest`: всё зелёное
