## 1. Setup

- [x] 1.1 Добавить таблицу `read_stats` в существующую SQLite-базу (CREATE TABLE IF NOT EXISTS …)
- [x] 1.2 Обновить модели в `src/core/models.py` (добавить Pydantic‑модель `ReadStat`)
- [x] 1.3 Добавить метод `add_reading_stat` в `src/core/database.py` для вставки записи о статистике чтения

## 2. Service Layer

- [x] 2.1 Реализовать `ReadingStatsService.add_record(book_id, pages_read, date)` в `src/core/services.py`
- [x] 2.2 Интегрировать вызов сервиса в метод обновления прогресса книги (`BookService.update_progress`)

## 3. Tests

- [x] 3.1 Тестировать добавление записи в `read_stats` через `ReadingStatsService`

## 4. Documentation & Cleanup

- [x] 4.1 Очистить временные файлы и проверить линтер (`flake8`)
