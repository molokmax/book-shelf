## Why

Обработка сообщений внутри команд устроена одинаково в семи многошаговых хендлерах, но каждый реализует каркас сам: вход по `is_active()`, диспетчеризация по `state` (`dict` в `/add`, `if/elif` в `/edit`, `getattr(f"_handle_{state}")` в `/list`), финал «отправить сообщение → удалить стейт» с комментарием, скопированным в восьми местах. Имена шагов — свободные строки, разбросанные по хендлерам и флоу.

Из-за отсутствия общего каркаса гард «не перехватывай чужой сценарий» из AGENTS.md реализован по-разному и с ошибками: `edit.py` и `details.py` возвращают `True` и молча теряют сообщение, `list.py` падает с `AttributeError` (роутер логирует, пользователь ничего не получает), `/add` во время `/edit` сбрасывает чужой сценарий с текстом «Добавление книги сброшено», `/start` оставляет чужой стейт висеть, неизвестное состояние в `/add` сбрасывается, а в остальных командах молча игнорируется.

Issue #41: рассмотреть паттерн StateMachine. Решение — гибрид «базовый класс сценария + явные переходы» (вариант D+B из обсуждения).

## What Changes

- `AbstractCommandHandler.handle()` становится шаблонным методом: гард чужого сценария, затем `_handle()`. Добавляются атрибуты `scenario_command` (каноническая команда сценария, `None` у одношаговых) и `is_system` (только `/start`, `/cancel`).
- Новый `ScenarioHandler` (`src/vk_bot/handlers/scenario.py`): `start`/`begin`, `goto`, `finish`, `reset_unknown_state`; диспетчеризация шагов по соглашению `step_<state>`, необязательные рендеры `render_<state>`, полнота покрытия проверяется в `__init_subclass__`.
- Новый `src/vk_bot/states.py`: `StrEnum` для шагов всех сценариев и для общих шагов под-сценариев (теги, выбор книги, прогресс). Значения совпадают с текущими строками — формат стейта и данные в `user_state` не меняются, миграция не нужна.
- Семь многошаговых хендлеров (`/add`, `/edit`, `/details`, `/list`, `/progress`, `/goal`, `/settings`) переводятся на `ScenarioHandler`; одношаговые (`/help`, `/stats`, `/export`, `/more`) остаются на `AbstractCommandHandler` и получают `_handle`.
- Единая политика при активном чужом сценарии: любая несистемная команда блокируется сообщением «⚠️ Сейчас активна другая операция. Заверши её или нажми «Отмена».», состояние не меняется. `/start` — исключение: сбрасывает сценарий и показывает приветствие. `/cancel` работает глобально, как сейчас.
- Повторный ввод команды того же сценария (`/add` во время `/add`) перезапускает сценарий с начального шага.
- Неизвестное состояние сбрасывается единообразно: финальное сообщение «⚠️ Не удалось продолжить сценарий. Начни заново: <команда>» с главной клавиатурой и удаление стейта.
- Флоу (`TagEditingFlow`, `BookSelectionFlow`, `ProgressUpdateFlow`) сохраняют контракт и колбэки; меняются только строковые литералы состояний на константы из `states.py`.
- Роутер не меняется: два прохода и приоритеты остаются. В AGENTS.md правило ручного гарда заменяется описанием поведения базового класса.

## Capabilities

### New Capabilities

- `scenario-machine`: жизненный цикл многошаговой команды — владение сценарием, вход, шаги, переходы, финал, повторный ввод команды, неизвестное состояние, общие под-сценарии.

### Modified Capabilities

- `main-menu`: требование «Не перехватывать чужие сценарии» для кнопок «Ещё»/«Назад» заменяется блокировкой с сообщением об отказе (раньше сообщение уходило в чужой сценарий).

## Impact

- `src/vk_bot/handlers/base.py`: шаблонный `handle()`, `_handle()`, `scenario_command`, `is_system`, отказ чужому сценарию
- `src/vk_bot/handlers/scenario.py`: новый `ScenarioHandler`
- `src/vk_bot/states.py`: новый модуль с `StrEnum`-состояниями
- `src/vk_bot/handlers/{add,edit,details,list,progress,goal,settings}.py`: переход на `ScenarioHandler`
- `src/vk_bot/handlers/{start,cancel,help,stats,export,more}.py`: `handle` → `_handle`, `is_system` у `/start` и `/cancel`, сброс стейта в `/start`
- `src/vk_bot/flows/{tag_editing,book_selection,progress_update}.py`: строковые состояния → константы
- `tests/test_handler_base.py`, новый `tests/test_scenario_handler.py`, новый `tests/handlers/test_handlers_guard.py`; обновление `tests/handlers/test_more_handler.py`, `test_settings_handler.py`, `test_goal_handler.py`, `test_progress_handler.py`, `test_add_handler.py`, `test_edit_handler.py`, `test_details.py`, `test_details_filter.py`, `test_list.py`
- `AGENTS.md`: раздел про обработку сообщений внутри команды
- `CONTEXT.md`: термины «Сценарий», «Шаг сценария»
- `docs/project_structure.md`: новые модули `states.py`, `handlers/scenario.py`
