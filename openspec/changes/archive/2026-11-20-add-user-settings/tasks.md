## 1. Модель и база данных

- [x] 1.1 Константы в `src/core/models.py`: `READING_SPEED_PERIODS = (7, 14, 30)`, `DEFAULT_READING_SPEED_PERIOD = 30`
- [x] 1.2 `CREATE TABLE IF NOT EXISTS user_settings` в `_create_tables` (`src/core/database.py`) со схемой из design.md (PK `user_id`, CHECK на набор значений, FK на `users`)
- [x] 1.3 Тест: таблица создаётся, повторная инициализация базы идемпотентна

## 2. Репозиторий и сервис настроек

- [x] 2.1 `UserSettingsRepository` в `src/core/repository.py`: `get_reading_speed_period(user_id) -> int` (30 при отсутствии строки), `set_reading_speed_period(user_id, days)` (upsert, обновление `updated_at`)
- [x] 2.2 `UserSettingsService` в `src/core/services.py`: `get`/`set` периода, `set` валидирует `days in READING_SPEED_PERIODS` (иначе `ValueError`)
- [x] 2.3 Тесты `tests/test_user_settings_service.py`: дефолт 30 без строки; первая установка; повторная установка (upsert, одна строка, обновлённый `updated_at`); некорректное значение; привязка к существующему `users.id`

## 3. Скорость чтения по периоду пользователя

- [x] 3.1 `ReadingStatsService.__init__`: создать `UserSettingsRepository` (сигнатура конструктора не меняется)
- [x] 3.2 `avg_pages_per_day`: период по `book.user_id`, `from_date = max(today - timedelta(days=period - 1), reading_start_date)`; сигнатура метода не меняется; `predict_days_to_completion` и порог скачка получают период автоматически
- [x] 3.3 `utils/helpers.py`: параметр `period_days: int = 30` в `format_book_details` и `format_progress_stats`, строка `Среднее за {period_days} дней: {avg:.2f} стр/день`
- [x] 3.4 `handlers/details.py` и `flows/progress_update.py`: период из `UserSettingsService`, передача `period_days` в форматтер
- [x] 3.5 Тесты: `avg_pages_per_day` за 7/14/30; дефолт 30 без строки; окно не раньше `reading_start_date`; прогноз по периоду; форматтеры с `period_days`

## 4. Обработчик /settings

- [x] 4.1 `src/vk_bot/handlers/settings.py`: `SettingsHandler` (priority 10, `commands = ["/settings"]`) с гардом чужого сценария (`return None`, если активен стейт другой команды)
- [x] 4.2 Вход: `get_or_create_user`, состояние `{"command": "/settings", "state": "menu", "data": {"user_id": ...}}`, экран настроек (текст из design.md, п. 6) с клавиатурой «7 дней» / «14 дней» / «30 дней» + «Назад»
- [x] 4.3 Состояние `menu`: выбор значения применяет его (upsert), отправляет «Период скорости чтения: N дней» с клавиатурой настроек, сценарий остаётся активен; «Назад» (своё, не через CancelHandler): `delete_state()`, «Возврат в главное меню» + `main_keyboard()`; прочий текст: `format_invalid_input` с подсказкой, без выхода из сценария
- [x] 4.4 Зарегистрировать `SettingsHandler` в `src/vk_bot/bot.py`
- [x] 4.5 Тесты `tests/handlers/test_settings_handler.py`: вход и экран с текущим значением; выбор 7/14/30 (сообщение, клавиатура, сценарий активен, значение в БД); повторный выбор; «Назад» (сообщение, главная клавиатура, состояние удалено); некорректный ввод; гард чужого сценария; набранная «отмена» работает через `CancelHandler`

## 5. Клавиатура, help, README

- [x] 5.1 `main_keyboard()`: последний ряд `/goal` / `/stats` / `/help` / `/settings`
- [x] 5.2 `handlers/help.py`: строка о `/settings` (настройка периода скорости чтения)
- [x] 5.3 `README.md`: пункт о настройках

## 6. Документация и проверка

- [x] 6.1 `CONTEXT.md`: термины «Настройки пользователя», «Период скорости чтения»; обновить определение «Скорость чтения» (среднее за период скорости чтения вместо «за последние 30 дней»)
- [x] 6.2 Обновить существующие тесты, где захардкожена строка «Среднее за 30 дней» (`tests/test_helpers.py`, `tests/handlers/test_details*.py`, `tests/flows/test_progress_update.py`)
- [x] 6.3 Прогнать `isort .`, `black .`, `flake8 src/`, `pytest`: всё зелёное
