## 1. Модель и база данных

- [x] 1.1 В `src/core/models.py`: dataclass `MotivationPhrase` (id, text, category, created_at), константы `PHRASE_CATEGORIES` и `GENERAL_PHRASE_CATEGORY` ("general"), dataclass `MotivationContext` (previous_page, new_page, pages_delta, finished, goal_completed)
- [x] 1.2 В `src/core/database.py` добавить таблицу `motivational_phrases` в `Database._create_tables` (DDL из design.md)
- [x] 1.3 В `src/core/migrations.py`: миграция `add_user_settings_motivation_column(conn)` (`PRAGMA table_info` + `ALTER TABLE user_settings ADD COLUMN motivation_enabled INTEGER NOT NULL DEFAULT 1`), вызов из `Database.__init__`
- [x] 1.4 В `src/core/migrations.py`: миграция `seed_motivational_phrases(conn)` (15 фраз из design.md, `INSERT OR IGNORE`, категория `general`), вызов из `Database.__init__`

## 2. Репозиторий и сервисы

- [x] 2.1 В `src/core/repository.py`: `MotivationPhraseRepository.get_random_phrase() -> str | None` (одна случайная фраза, `None` на пустой таблице)
- [x] 2.2 В `src/core/repository.py` в `UserSettingsRepository`: `get_motivation_enabled(user_id) -> bool` (нет строки = включена) и `set_motivation_enabled(user_id, enabled)` (upsert: сохранить `created_at`, обновить `updated_at`, поведение периода не меняется)
- [x] 2.3 В `src/core/services.py`: `MotivationService.pick_phrase(context: MotivationContext) -> str | None` (v1-стратегия игнорирует контекст) и в `UserSettingsService`: `is_motivation_enabled`, `set_motivation_enabled`

## 3. Показ фразы при обновлении прогресса

- [x] 3.1 В `ProgressUpdateFlow._finish_progress_update`: собирать `MotivationContext` (previous_page известен на месте, unchanged = ввод текущей страницы, pages_delta, finished = книга переходит в «прочитал», goal_completed = запишется из строки цели); при активном сценарии: проверка `is_motivation_enabled`, условие показа (не `unchanged` и нет строки «🎉 Цель на день выполнена!»), фраза последним блоком `parts`; сбой сервиса не ломает подтверждение
- [x] 3.2 Отсутствие состояния previous_page для пути `unchanged` соответствует правилу «фразу не показываем», ветка не добавляет лишние обращения к БД

## 4. Экран настроек

- [x] 4.1 В `SettingsHandler`: строка «Мотивация: включена/выключена» в тексте экрана (`_format_settings_screen` получает состояние из сервиса), состояние `data` хранит `user_id` как сейчас
- [x] 4.2 В `SettingsHandler._create_settings_keyboard`: кнопка-переключатель во втором ряду рядом с «30 дней», цвет `PRIMARY` при вкл / `SECONDARY` при выкл; «Назад» уходит в третий ряд
- [x] 4.3 В `SettingsHandler._handle_menu`: матчинг кнопки «Мотивация: Вкл» / «Мотивация: Выкл» (casefold, как у периодов); после тоггла ответ «Мотивация включена» / «Мотивация: выключена», сценарий остаётся активен
- [x] 4.4 Проверить, что посторонний текст в меню получает «Выбери значение из клавиатуры», а «Назад» работает как раньше

## 5. Тесты

- [x] 5.1 В `tests/flows/test_progress_update.py`: фраза добавляется при включённой настройке и изменившемся прогрессе; нет при `unchanged`; нет при строке «🎉 Цель на день выполнена!»; нет при выключенной настройке; сбой сервиса не ломает подтверждение
- [x] 5.2 В `tests/handlers/test_settings_handler.py`: экран содержит строку состояния и метку кнопки; тоггл сохраняет противоположное значение и меняет текст ответа; раскраска кнопки соответствует состоянию
- [x] 5.3 В `tests/test_migrations.py`: сид идемпотентен (15 строк без дублей при повторе); колонка `motivation_enabled` добавляется в базу без неё и не мешает существующим строкам
- [x] 5.4 Новый `tests/test_motivation_service.py`: репозиторий выбирает фразу из списка и `None` на пустой базе; `UserSettingsService.is_motivation_enabled` (дефолт и переключение), `set_motivation_enabled` (upsert, период не трогается); sqlite в `tmp_path` по образцу `tests/test_user_settings_service.py`

## 6. Документация и финализация

- [x] 6.1 `CONTEXT.md`: термины «Мотивационная фраза» и «Категория фразы» (формат глоссария существующего файла)
- [x] 6.2 `README.md`: строка фичи про случайную мотивационную фразу после обновления прогресса и тоггл в `/settings`
- [x] 6.3 Прогнать `openspec validate add-motivational-phrases --strict`; отметить выполненные задачи в tasks.md
- [x] 6.4 Прогнать `isort .`, `black .`, `flake8 src/`, `pytest`; исправить замечания
