## Why

Скорость чтения захардкожена: окно усреднения 30 дней зашито в `ReadingStatsService.avg_pages_per_day` (`src/core/services.py`), и его нельзя менять. Пользователи читают с разной регулярностью: тем, кто читает каждый день, окно 30 дней размывает актуальный темп, тем, кто с паузами, окно 7 дней занижает. Нужны персональные настройки приложения (issue #64), первая из них: за сколько дней считать среднее количество прочитанных страниц.

## What Changes

- Новая команда `/settings`: экран с текущими значениями настроек и клавиатурой изменения. Сейчас настройка одна: период скорости чтения (7 / 14 / 30 дней, по умолчанию 30).
- Новая типизированная таблица `user_settings` (одна строка на пользователя). Отсутствие строки означает период 30, поэтому поведение существующих пользователей не меняется и миграция данных не нужна.
- Скорость чтения считается за период из настроек пользователя и меняется во всех местах использования: детальная информация о книге, мини-статистика обновления прогресса, прогноз завершения, порог скачка прогресса. Строка статистики выводится как «Среднее за N дней».
- Кнопка `/settings` в главной клавиатуре (четвёртая в последнем ряду), строка в `/help`.
- Термины в `CONTEXT.md`: «Настройки пользователя», «Период скорости чтения»; обновлено определение «Скорость чтения».

## Capabilities

### New Capabilities

- `user-settings`: хранение и изменение персональных настроек через команду `/settings`; управление периодом скорости чтения.

### Modified Capabilities

<!-- Нет изменяемых существующих capability на уровне spec: в openspec/specs есть только vk-export-csv. Влияние на скорость чтения описано в design.md. -->

## Impact

- `src/core/models.py`: константы `READING_SPEED_PERIODS`, `DEFAULT_READING_SPEED_PERIOD`
- `src/core/database.py`: таблица `user_settings` в `_create_tables`
- `src/core/repository.py`: `UserSettingsRepository` (`get`/`set` периода, upsert)
- `src/core/services.py`: `UserSettingsService`; `ReadingStatsService` резолвит период по `book.user_id`
- `src/utils/helpers.py`: параметр `period_days` в `format_book_details` / `format_progress_stats`, строка «Среднее за {N} дней»
- `src/vk_bot/handlers/settings.py`: новый `SettingsHandler` (состояние `menu`)
- `src/vk_bot/handlers/details.py`, `src/vk_bot/flows/progress_update.py`: передача периода в форматтеры
- `src/vk_bot/keyboards.py`: кнопка `/settings` в `main_keyboard()`
- `src/vk_bot/handlers/help.py`: строка о `/settings`
- Тесты: `tests/handlers/test_settings_handler.py`, `tests/test_user_settings_service.py`, обновление `tests/test_reading_stats*.py`, `tests/test_helpers.py`, `tests/flows/test_progress_update.py`
- `CONTEXT.md`, `README.md`
