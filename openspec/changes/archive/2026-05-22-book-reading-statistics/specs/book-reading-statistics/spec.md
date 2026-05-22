## ADDED Requirements

### Requirement: book-reading-statistics
Система ДОЛЖНА отслеживать количество прочитанных страниц для каждой книги, фиксируя дату и время обновления.

#### Scenario: Обновление прогресса книги
- **WHEN** пользователь обновляет прогресс чтения книги через сервис `BookService.update_progress`
- **THEN** система запишет новую запись в таблицу `read_stats` со значением `pages_read` и текущей датой (`read_date`).
