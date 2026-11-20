## 1. Модель и база данных

- [x] 1.1 Добавить модель `Goal` (id, user_id, kind, target, created_at, updated_at) в `src/core/models.py`; добавить поле `user_id: Optional[str]` в `ReadStat`
- [x] 1.2 Добавить `CREATE TABLE IF NOT EXISTS goals` в `_create_tables` (`src/core/database.py`) со схемой из design.md
- [x] 1.3 Добавить `add_read_stats_user_id(conn)` в `src/core/migrations.py`: идемпотентное `ALTER TABLE read_stats ADD COLUMN user_id TEXT` + заливка NULL-строк из `books`
- [x] 1.4 Вызвать `add_read_stats_user_id` в `Database.__init__` рядом с `add_link_column`
- [x] 1.5 Обновить `add_reading_stat` и маппинг `ReadStat` в `src/core/database.py` (запись и чтение `user_id`)

## 2. Репозитории

- [x] 2.1 В `src/core/repository.py`: `GoalRepository` (get по user_id+kind, upsert, delete) с обновлением `updated_at`
- [x] 2.2 В `ReadStatsRepository`: параметр `user_id` в `add_reading_stats`; новый метод суммы страниц по пользователю за период (`fetch_pages_by_user`)

## 3. Сервисы

- [x] 3.1 Новый `GoalService` в `src/core/services.py`: `get_goal`, `set_daily_goal`, `disable_goal`, `today_pages(user_id)`, `get_goal_status` (goal, today, percent, completed, remaining)
- [x] 3.2 `ReadingStatsService.add_record` принимает и прокидывает `user_id`
- [x] 3.3 `BookService.update_book_progress` передаёт `book.user_id` в `add_record`
- [x] 3.4 Юнит-тесты `GoalService` на уровне БД (`tests/test_goal_service.py`): установка/изменение/отключение, сумма за день по всем книгам, вчерашние записи не учитываются, NULL user_id не учитывается

## 4. Обработчик /goal

- [x] 4.1 Создать `src/vk_bot/handlers/goal.py`: `GoalHandler` (priority 10, commands `/goal`, `goal`, `цель`) с гардом чужого сценария (`return None`, если активен стейт другой команды)
- [x] 4.2 Состояния сценария: меню («Просмотр»/«Установить»/«Отключить»/«Отмена»), ввод числа; завершение любого действия — подтверждение, главная клавиатура, `delete_state()`
- [x] 4.3 Просмотр: экран цели (цель, сегодня, процент, остаток или «Выполнена»; без цели — «Цель не установлена»)
- [x] 4.4 Установка: целое `>= 1` — сохранить; `0` — отключить; иначе ошибка с подсказкой без выхода из сценария
- [x] 4.5 Зарегистрировать `GoalHandler` в `src/vk_bot/bot.py`; добавить кнопку `/goal` в `main_keyboard()` (первой в ряду со `/stats` и `/help`); добавить строку о `/goal` в `/help`
- [x] 4.6 Тесты `tests/handlers/test_goal_handler.py` по сценариям спеки: меню, просмотр (с целью/без/выполнена), установка (корректно/0/ошибка), отключение (с целью/без), гард чужого сценария

## 5. Прогресс цели при обновлении прогресса

- [x] 5.1 В `ProgressUpdateFlow._apply_progress` зафиксировать дельту обновления и передать её в `_finish_progress_update`
- [x] 5.2 В `_finish_progress_update`: если цель есть — строка `Цель на день: X/Y стр.` (без эмодзи) в обоих вариантах финала; при пересечении порога (дельта > 0, до < цели <= после) — `🎉 Цель на день выполнена! Сегодня прочитано X из Y страниц.` вместо строки
- [x] 5.3 Если цели нет — сообщение без изменений
- [x] 5.4 Тесты `tests/flows/test_progress_update.py`: строка о цели, отсутствие строки без цели, поздравление при пересечении, отсутствие поздравления при повторном обновлении и при дельте 0

## 6. Миграция и совместимость

- [x] 6.1 Тест миграции: на старой базе без колонки заливка `user_id` из `books`; повторный запуск идемпотентен (`tests/test_migrations.py`)
- [x] 6.2 Обновить существующие тесты статистики под новые сигнатуры (`tests/test_reading_stats*.py`)

## 7. Документация и проверка

- [x] 7.1 `CONTEXT.md`: термины «Дневная цель», «Прогресс дня», «Выполнение цели» по формату глоссария
- [x] 7.2 `README.md`: пункт о команде `/goal` и дневных целях
- [x] 7.3 `AGENTS.md`: зафиксировать механизм «обработчик не перехватывает сообщения из активного сценария другой команды» (гард `command != <своя>`, системные команды — исключение)
- [x] 7.4 Прогнать `isort .`, `black .`, `flake8 src/`, `pytest` — всё зелёное
- [x] 7.5 Создать issue про учёт часовых поясов пользователя (цель привязана к серверному времени)
