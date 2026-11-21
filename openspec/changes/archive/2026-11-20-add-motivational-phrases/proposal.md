## Why

После обновления прогресса бот отвечает сухим подтверждением и статистикой. Единственный поощрительный элемент (поздравление о выполненной дневной цели) срабатывает только в момент выполнения цели (issue #47). Нужны регулярные подбадривающие сообщения после каждого обновления прогресса: они поддерживают привычку чтения, а не только факт достижения цели.

## What Changes

- Новая таблица `motivational_phrases` (глобальный список фраз, одна колонка категории под будущий сценарный подбор) с начальным списком из 15 фраз, добавляемым идемпотентной миграцией.
- Сервис выбора фразы `MotivationService.pick_phrase(context)`: в v1 стратегия «случайная фраза», контекст обновления принимается как шов под будущие сценарии (тренд страниц, цель, завершение книги).
- После успешного обновления прогресса в то же сообщение добавляется случайная фраза последним блоком. Не показывается: при «Прогресс не изменился» и когда уже есть строка «🎉 Цель на день выполнена!».
- Новая настройка `motivation_enabled` (по умолчанию включена): колонка в `user_settings`, тоггл-кнопка на экране `/settings`.
- Термины в `CONTEXT.md`: «Мотивационная фраза», «Категория фразы»; строка фичи в `README.md`.

## Capabilities

### New Capabilities

- `motivation`: хранение мотивационных фраз (таблица, категории, открытый список через миграции) и показ случайной фразы в отклике на обновление прогресса.

### Modified Capabilities

<!-- user-settings ещё не в openspec/specs: capability заведена дельтой активного change add-user-settings, поэтому маркер ADDED, не MODIFIED. При архивации обеих изменений требования смёржатся. -->

- `user-settings`: новая настройка «Мотивация» (вкл/выкл) на экране `/settings`, по умолчанию включена.

## Impact

- `src/core/models.py`: dataclass `MotivationPhrase`, константы категорий фраз
- `src/core/database.py`: таблица `motivational_phrases` в `_create_tables`, колонка `motivation_enabled` в `user_settings`
- `src/core/migrations.py`: сид 15 фраз (идемпотентно), добавление колонки `motivation_enabled` для существующих БД
- `src/core/repository.py`: `MotivationPhraseRepository.get_random_phrase()`, метод тоггла в `UserSettingsRepository`
- `src/core/services.py`: `MotivationService.pick_phrase(context)`, проверка включённости в `UserSettingsService`
- `src/vk_bot/flows/progress_update.py`: блок фразы в `_finish_progress_update`
- `src/vk_bot/handlers/settings.py`: строка состояния в тексте, тоггл-кнопка с динамической меткой
- Тесты: `tests/flows/test_progress_update.py`, `tests/handlers/test_settings_handler.py`, `tests/test_migrations.py`, `tests/test_motivation_service.py`
- `CONTEXT.md`, `README.md`
