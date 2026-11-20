## 1. Каркас сценария

- [x] 1.1 `src/vk_bot/states.py`: `StrEnum`-перечисления шагов — общие (`SelectionState`, `TagState`, `ProgressState`) и сценарные (`AddState`, `EditState`, `DetailsState`, `ListState`, `ProgressScenarioState`, `GoalState`, `SettingsState`); значения дословно совпадают с текущими строками
- [x] 1.2 `src/vk_bot/handlers/base.py`: `handle()` — шаблонный метод (гард чужого сценария → `_handle()`), атрибуты `scenario_command` и `is_system`, отказ через `api.messages.send` без клавиатуры и без `message_chain`; `_handle()` — абстрактный
- [x] 1.3 `src/vk_bot/handlers/scenario.py`: `ScenarioHandler` — `initial_state`, `states`, `start`, `begin`, `goto`, `finish`, `reset_unknown_state`, диспетчеризация `step_<state>` и `render_<state>`, проверка полноты в `__init_subclass__`
- [x] 1.4 `tests/test_handler_base.py`: тесты гарда (чужой сценарий → отказ и `True`, стейт не меняется; системные команды проходят; пустой `command` не блокирует)
- [x] 1.5 `tests/test_scenario_handler.py`: вход, переход, `None` остаётся в шаге, финал в порядке «сообщение → удаление», неизвестный шаг, перезапуск по своей команде, `TypeError` при пропущенном `step_*`

## 2. Гард и одношаговые хендлеры

- [x] 2.1 `handlers/start.py`: `is_system = True`, сброс состояния в `_handle` после отправки приветствия
- [x] 2.2 `handlers/cancel.py`: `is_system = True`, поведение без изменений
- [x] 2.3 `handlers/help.py`, `handlers/stats.py`, `handlers/export.py`, `handlers/more.py`: `handle` → `_handle`, старый гард в `more.py` удаляется
- [x] 2.4 `tests/handlers/test_handlers_guard.py`: параметризованный тест — каждая несистемная команда при чужом сценарии отвечает отказом и не меняет стейт
- [x] 2.5 Обновить тесты, ожидавшие `None` при чужом сценарии: `tests/handlers/test_more_handler.py`, `test_settings_handler.py`, `test_goal_handler.py`, `test_progress_handler.py`

## 3. Миграция сценариев на ScenarioHandler

- [x] 3.1 `handlers/goal.py`: шаги `menu`, `waiting_for_goal_input`; финал через `finish`
- [x] 3.2 `handlers/settings.py`: шаг `menu`; «Назад» — финал с главной клавиатурой
- [x] 3.3 `handlers/list.py`: шаги `choose_filter`, `choose_status`, `choose_tag`; убрать `getattr(f"_handle_{state}")`
- [x] 3.4 `handlers/add.py`: шаги `choose_method`, `waiting_for_title/author/pages/link`, `selecting_tags`, `waiting_for_litres_url/confirm`; `_STATE_DISPATCH` заменяется каркасом
- [x] 3.5 `handlers/details.py`: шаги `choose_filter`, `selecting_status_filter`, `selecting_tag_filter`, `selecting_book`
- [x] 3.6 `handlers/edit.py`: шаги `choose_filter`, `selecting_status_filter`, `selecting_tag_filter`, `selecting_book`, `selecting_action`, `editing_title/author/pages/link`, `selecting_tags`, `selecting_status`
- [x] 3.7 `handlers/progress.py`: шаги `selecting_reading_book`, шаги выбора книги и обновления прогресса (делегируются флоу)
- [x] 3.8 Обновить тесты сценариев: `test_add_handler.py`, `test_details.py`, `test_details_filter.py`, `test_edit_handler.py`, `test_list.py`, `test_goal_handler.py`, `test_settings_handler.py`, `test_progress_handler.py` — при необходимости только способ установки состояния

## 4. Флоу на общие состояния

- [x] 4.1 `flows/tag_editing.py`: `selecting_tags` → `TagState.SELECTING_TAGS`
- [x] 4.2 `flows/book_selection.py`: `choose_filter`, `selecting_status_filter`, `selecting_tag_filter`, `selecting_book` → `SelectionState`
- [x] 4.3 `flows/progress_update.py`: `waiting_for_progress_input`, `waiting_for_progress_confirm` → `ProgressState`; финал флоу оставлен внутри `ProgressUpdateFlow` (контракт флоу не менялся, владельца флоу не знает)
- [x] 4.4 Тест-инвентарь `tests/test_states.py`: значения общих состояний совпадают во флоу и в перечислениях сценариев, дублей нет

## 5. Документация

- [x] 5.1 `AGENTS.md`: правило ручного гарда заменяется описанием шаблонного метода, `ScenarioHandler`, `step_<state>`/`render_<state>` и системных команд
- [x] 5.2 `CONTEXT.md`: термины «Сценарий», «Шаг сценария»; уточнено, что команды других сценариев блокируются кроме `/start` и `/cancel`
- [x] 5.3 `docs/project_structure.md` в репозитории отсутствует: структура `src/vk_bot` (включая `states.py` и `handlers/scenario.py`) обновлена в `AGENTS.md`

## 6. Проверка

- [x] 6.1 `isort .`, `black .`, `flake8 src/` — без замечаний
- [x] 6.2 `pytest` — 285 тестов зелёные; сценарии покрыты существующими тестами хендлеров и флоу (`/add`, `/add` с LitRes, `/edit` со сменой статуса, `/details`, `/list`, `/progress` с подтверждением скачка, `/goal`, `/settings`)
- [ ] 6.3 Ручной чек-лист в VK: чужая команда в сценарии даёт отказ; `/start` сбрасывает; `/cancel` работает; повторный `/add` не становится названием; теги и выбор книги возвращают в сценарий; промежуточные сообщения по-прежнему удаляются — требует токена и живого чата
- [x] 6.4 `npx @fission-ai/openspec validate refactor-scenario-state-machine` — «Change is valid»
