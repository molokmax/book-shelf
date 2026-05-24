## 1. Service Layer

- [x] 1.1 Добавить функцию `get_reading_stats(book_id: int, from_date: datetime, to_date: datetime) -> int` в `src/core/services.py`.
- [x] 1.2 Реализовать логику вычисления среднего количества страниц за последние 30 дней (`avg_pages_per_day`).
- [x] 1.3 Реализовать метод `predict_completion_date(book_id: int) -> date` в сервисе, использующий `remaining_pages / avg_pages_per_day`.

## 2. Repository Layer

- [x] 2.1 Создать класс `ReadStatsRepository` в `src/core/repository.py` с методом `fetch_reading_stats(book_id: int, from_date: datetime, to_date: datetime) -> int`.
- [x] 2.2 Добавить метод `fetch_average_pages_per_day(book_id: int, days: int = 30) -> float` для расчёта среднего за последние 30 дней.

## 3. Bot Handler Updates

- [x] 3.1 В `src/vk_bot/handlers/details.py` вызвать `services.get_reading_stats` для периодов 7 и 30 дней и добавить результаты в ответ.
- [x] 3.2 В том же обработчике вызвать `services.predict_completion_date` и вывести сообщение «Ожидаемая дата завершения чтения: <date>».
- [x] 3.3 Добавить обработку случая, когда `avg_pages_per_day` == 0 → сообщение «Недостаточно данных для оценки завершения».

## 4. Tests

- [x] 4.1 В `tests/test_book_detail.py` добавить тесты для сервисных функций: проверка корректного подсчёта статистики за 7 и 30 дней.
- [x] 4.2 Добавить тест `test_predict_completion_date` с фиктивными данными, где `avg_pages_per_day` > 0 и < 0.
- [x] 4.3 Тестировать обработчик `details.py`: проверка включения статистики и прогноза в сообщение бота.
- [x] 4.4 Тестировать случай отсутствия данных → проверка сообщения «Недостаточно данных для оценки завершения».

## 5. Documentation & Logging

- [x] 5.1 Обновить `README.md` раздел «Статистика чтения», добавить описание новых возможностей.
- [x] 5.2 Добавить логирование DEBUG в новые методы репозитория и сервиса.
- [x] 5.3 Добавить примеры использования в `docs/project_structure.md` при необходимости.
