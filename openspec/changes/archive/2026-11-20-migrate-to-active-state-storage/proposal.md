## Why

Сейчас весь пользовательский стейт (текущая команда, шаг, данные формы) хранится в глобальном in-memory словаре `active_states`. При перезапуске бота стейт всех пользователей теряется. При этом уже существует `UserStateRepository` с SQLite-персистентностью, который остаётся неиспользованным. Нужно убрать технический долг: подключить SQLite-хранилище, предоставить удобную обёртку и дать доступ к стейту через `BotContext`.

## What Changes

- Перенести `UserStateRepository` из `src/vk_bot/repository/user_state.py` в `src/core/repository.py`, приведя к единому стилю репозиториев
- Создать `ActiveStateStorage` — обёртку над репозиторием с методами `get`, `save`, `delete`, `is_active`, а также управлением структурой стейта
- Добавить в `BotContext` методы `get_state()`, `set_state()`, `delete_state()`, `is_active()` и свойство `command_state`, делегирующие вызовы в `ActiveStateStorage`
- Заменить все прямые обращения к `active_states` в хендлерах, роутинге и `/cancel` на вызовы через `BotContext`
- Удалить in-memory `active_states` из `vk_bot/states.py`

## Capabilities

### New Capabilities
- `active-state-storage`: управление пользовательским стейтом через SQLite-персистентность с доступом через `BotContext`

### Modified Capabilities
<!-- Нет изменений требований на уровне specs — только внутренняя имплементация -->

## Impact

- **`src/core/repository.py`** — добавление `UserStateRepository`
- **`src/vk_bot/context.py`** — добавление методов работы со стейтом
- **`src/vk_bot/handlers/add.py`, `edit.py`, `details.py`, `list.py`, `cancel.py`** — замена `active_states` на контекст
- **`src/vk_bot/handlers/*_handler.py`** — замена проверок `active_states` на `context.is_active()`
- **`src/vk_bot/bot.py`** — замена fallback-проверки `active_states`
- **`src/vk_bot/states.py`** — удаление `active_states`
- **`src/vk_bot/repository/user_state.py`** — удаление (перенос в core)
- **Тесты** — обновление всех тестов, использующих `active_states`
