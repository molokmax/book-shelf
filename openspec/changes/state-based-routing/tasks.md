## 1. Модификация CommandRouter

- [x] 1.1 Изменить `CommandRouter.route()`: после того как ни один обработчик не совпал по `context.command`, проверить `context.is_active()`. Если активен, выполнить второй проход по обработчикам с `context.command_state`.
- [x] 1.2 Добавить тесты для `CommandRouter.route()` с активным стейтом

## 2. Удаление fallback-диспатчинга

- [x] 2.1 Удалить из `VkBookShelfBot.handle_event()` в `bot.py` блок кода после `router.route()`, который обрабатывает step-варианты команд `/list`, `/edit`, `/details`.
- [x] 2.2 Проверить, что все E2E-сценарии проходят (`pytest`)
