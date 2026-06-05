## Context

Команда `/stats` обрабатывается через fallback-ветку в `bot.py` прямой вызов функции `handle_stats_command` из `stats.py`. Это единственная команда, которая ещё не мигрирована на `AbstractCommandHandler`. Все остальные команды (`/add`, `/edit`, `/list`, `/details`, `/export`, `/help`) уже используют единый механизм маршрутизации через `CommandRouter`.

## Goals / Non-Goals

**Goals:**
- Перенести реализацию `/stats` в класс `StatsHandler` — наследник `AbstractCommandHandler`
- Зарегистрировать `StatsHandler` в `CommandRouter`
- Удалить старый файл `stats.py` и fallback-ветку в `bot.py`

**Non-Goals:**
- Изменение бизнес-логики команды `/stats` — форматирование сообщения, сервисный вызов и всё поведение остаётся идентичным
- Рефакторинг `BookService.get_stats()` или `ReadingStatsService`
- Изменение системы маршрутизации или `AbstractCommandHandler`

## Decisions

### Decision: Использовать однофазный обработчик (как HelpHandler / ExportHandler)

Команда `/stats` не имеет состояния — это однократный запрос-ответ без диалога. Однофазная реализация без `ActiveStateStorage` (как в `HelpHandler` и `ExportHandler`) — правильный выбор.

### Decision: Весь код переносится в новый файл, старый удаляется

Поскольку новый класс будет содержать ровно ту же логику, что и `handle_stats_command`, дублирование файлов не имеет смысла. Старый `stats.py` удаляется сразу.

## Risks / Trade-offs

- **[Низкий] Пропущенный импорт**: При удалении `from vk_bot.handlers.stats import handle_stats_command` из `bot.py` можно случайно оставить неиспользуемый импорт → *решено явным удалением всей ветки*
- **[Низкий] Конфликт имён**: Новый файл `stats_handler.py` следует конвенции именования, уже принятой в проекте (`add_handler.py`, `edit_handler.py` и т.д.)
