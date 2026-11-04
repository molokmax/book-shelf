## Why

Главная клавиатура (`main_keyboard()` в `src/vk_bot/keyboards.py`) выросла до 10 кнопок в 3 ряда: `/progress /edit /add`, `/list /details /export`, `/goal /stats /help /settings`. Ежедневные действия (обновить прогресс, посмотреть список, добавить книгу) делят экран с редкими (`/export`, `/goal`, `/settings`), главные команды требуют визуального поиска. Issue #73: оставить в главном меню только самые востребованные команды, остальные перенести в подменю «Ещё».

## What Changes

- Главное меню сокращается до 5 команд и кнопки «Ещё», 2 ряда: `/progress /details /list`, `/add /help «Ещё»». В подменю уходят `/edit`, `/export`, `/goal`, `/stats`, `/settings`.
- Кнопка «Ещё» с payload `{"command": "/more"}`: новый `MoreHandler` открывает экран «Ещё» (список команд с краткими описаниями) и клавиатуру подменю: `/edit /export /goal`, `/stats /settings «Назад»`. Навигация stateless: состояние в `user_state` не пишется.
- Кнопка «Назад» с payload `{"command": "/back"}`: возврат в главное меню, сообщение «Главное меню» с главной клавиатурой.
- `more_keyboard()` добавляется в `keyboards.py` рядом с `main_keyboard()`.
- `/start`: новый текст приветствия под состав главного меню и кнопку «Ещё». `/help`: добавляется строка о `/details` (сейчас команда в справке отсутствует, оставаясь в главном меню).
- Термины «Главное меню» и «Подменю „Ещё“» в `CONTEXT.md` (добавлены в grilling-сессии).

## Capabilities

### New Capabilities

- `main-menu`: состав главного меню, подменю «Ещё» и навигация между ними.

### Modified Capabilities

<!-- В openspec/specs единственная спека vk-export-csv, она не затронута: состав и поведение /export не меняются. -->

## Impact

- `src/vk_bot/keyboards.py`: новая раскладка `main_keyboard()`, новая `more_keyboard()`
- `src/vk_bot/handlers/more.py`: новый `MoreHandler` (`/more`, `/back`)
- `src/vk_bot/bot.py`: импорт и регистрация `MoreHandler`
- `src/vk_bot/handlers/start.py`: текст приветствия
- `src/vk_bot/handlers/help.py`: строка `/details`
- `tests/handlers/test_progress_handler.py`: обновление `test_main_keyboard_contains_progress_command`
- `tests/handlers/test_more_handler.py`: новые тесты хендлера и клавиатур
- `CONTEXT.md`: термины «Главное меню», «Подменю „Ещё“» (уже добавлены)
- `README.md` не затрагивается: состав меню в нём не описан, пункты о командах остаются корректными
