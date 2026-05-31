## 1. Implementation

- [x] 1.1 Обновить сервис `ReadingStatsService` и метод `fetch_reading_stats` в `ReadStatsRepository` для поддержки `datetime` в параметрах `from_date` и `to_date` (изменить типы аргументов).
- [x] 1.2 Обновить метод `fetch_average_pages_per_day` в `ReadStatsRepository`. Параметр `from_date` должен быть `datetime`. внутри функции вычисляется to_date. это должен быть конец текущего дня.
- [x] 1.3 Обновить обработчик команды `details` (src/bot/handlers/details.py) для передачи в to_date конца текущего дня.
- [x] 1.4 Обновить метод `get_reading_stats` в `ReadingStatsService` для поддержки параметра `to_date` типа `datetime`.

## 2. Tests

- [x] 2.1 Добавить тест, проверяющий, что при вызове `details` в тот же день учитываются новые страницы.
- [x] 2.2 Обновить существующие фикстуры/моки, если они зависят от параметров даты.
- [x] 2.3 Запустить полный набор тестов и убедиться, что все проходят.
