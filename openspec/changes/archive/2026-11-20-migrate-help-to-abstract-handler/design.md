## Context

Команда `/help` — последняя основная команда (наряду с `/start`, `/cancel`, `/stats`), которая обрабатывается через старый `if/elif` маршрут в `bot.py`. Пять других команд (`/add`, `/edit`, `/list`, `/details`, `/export`) уже мигрированы на `AbstractCommandHandler` и `CommandRouter`. Текущая реализация help — это standalone-функция `handle_help_command` в `src/vk_bot/handlers/help.py`.

## Goals / Non-Goals

**Goals:**
- Создать `HelpHandler(AbstractCommandHandler)` с `priority=10` и `commands=["/help", "help"]`
- Зарегистрировать `HelpHandler()` в `CommandRouter` в `VkBookShelfBot.__init__`
- Удалить импорт `handle_help_command` из `bot.py`
- Удалить `elif command == "/help"` из `handle_event`
- Удалить старый файл `src/vk_bot/handlers/help.py`

**Non-Goals:**
- Миграция команд `/start`, `/cancel`, `/stats` — выходят за рамки этого change
- Изменение текста справки или функциональности help
- Рефакторинг `help.py` перед удалением

## Decisions

| Решение | Альтернативы | Обоснование |
|---|---|---|
| **Inline-реализация** (весь код из `help.py` переносится в `HelpHandler.handle`) | Wrapper-паттерн (вызов `handle_help_command`) | Старый файл `help.py` удаляется полностью, а не остаётся как зависимость; код становится самодостаточным, как в `ExportHandler` |
| **priority=10** | Другой приоритет | Единый приоритет для всех хендлеров команд (`AddHandler`, `EditHandler`, `ListHandler`, `DetailsHandler`, `ExportHandler` — все `priority=10`) |
| **commands=["/help", "help"]** | Только `/help` | Соответствует паттерну остальных хендлеров (поддержка команды как с `/`, так и без) |

## Risks / Trade-offs

- **[Низкий] Двойной импорт**: Если забыть удалить старый импорт и `elif`-ветку, команда `/help` сработает дважды. **Mitigation**: После создания `HelpHandler` сразу удаляем старый код до запуска.
- **[Низкий] Тесты**: Старые тесты могут ссылаться на `help.py`. **Mitigation**: Обновить импорты в тестах при необходимости.
