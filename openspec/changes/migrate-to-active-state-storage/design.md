## Context

Сейчас пользовательский стейт управляется через глобальный in-memory словарь `active_states` в `vk_bot/states.py`. Он теряется при перезапуске бота. В коде уже есть `UserStateRepository` с SQLite-персистентностью, но он не используется — лежит в `vk_bot/repository/user_state.py` и не имеет метода `delete_state`. Все репозитории (Book, User, ReadStats) находятся в `core/repository.py`, а `UserStateRepository` — единственный, кто создаёт свой собственный экземпляр `Database()` без возможности инъекции.

`BotContext` (`vk_bot/context.py`) — тонкая обёртка над VK-событием без какого-либо доступа к стейту. Хендлеры импортируют `active_states` напрямую и мутируют его.

## Goals / Non-Goals

**Goals:**
- Перенести `UserStateRepository` в `core/repository.py` в едином стиле с остальными репозиториями
- Добавить метод `delete_state` в репозиторий
- Создать `ActiveStateStorage` — удобную обёртку с методами `get`, `save`, `delete`, `is_active` и хелперами для работы со структурой стейта
- Добавить в `BotContext` методы `get_state()`, `set_state()`, `delete_state()`, `is_active()` и свойство `command_state`
- Заменить все прямые обращения к `active_states` на вызовы через `BotContext`
- Удалить `active_states` и сам файл `vk_bot/states.py`
- Обновить тесты

**Non-Goals:**
- Изменение схемы данных `user_state` (JSON-блок остаётся)
- Рефакторинг логики хендлеров (только замена источника стейта)
- Изменение `CommandRouter` или других частей бота, не связанных со стейтом
- Добавление кэширования (каждый запрос читает из SQLite)

## Decisions

### 1. Где создавать `ActiveStateStorage`

**Решение**: Создать экземпляр `ActiveStateStorage` в `bot.py` и передавать в конструктор `BotContext`.

Альтернативы:
- **Модульный singleton**: Плохо — тесты не смогут замокать стейт без глобального сброса.
- **Lazy-инициализация в BotContext**: Приемлемо, но `BotContext` тогда знает о конфигурации БД, что размывает ответственность.

`ActiveStateStorage` будет создан один раз в `VkBookShelfBot.__init__` и передан в `BotContext` при каждом событии.

### 2. Архитектура `ActiveStateStorage`

```
ActiveStateStorage
  └── UserStateRepository (core.repository)
        └── Database (core.database)
```

`UserStateRepository` хранит базовые CRUD-операции (get, save, delete). `ActiveStateStorage` добавляет:
- `is_active(user_id) -> bool` — проверка наличия непустого стейта
- `get_command(user_id) -> str | None` — команда из стейта
- `get_state(user_id) -> str | None` — шаг из стейта
- `new_state(command: str, state: str, data: dict) -> dict` — фабрика структуры стейта

### 3. Изменение `BotContext`

В `__slots__` добавляется `_storage: ActiveStateStorage`. Конструктор принимает `storage`.

Методы:
- `get_state() -> dict` — делегирует `_storage.get(user_id)`
- `set_state(state: dict)` — делегирует `_storage.save(user_id, state)`
- `delete_state()` — делегирует `_storage.delete(user_id)`
- `is_active() -> bool` — делегирует `_storage.is_active(user_id)`
- `command_state -> str | None` — делегирует `_storage.get_command(user_id)`

### 4. Замена `active_states` в хендлерах

**Паттерн замены**:
```python
# Было:
from vk_bot.states import active_states
active_states[user_id] = {"command": "/add", "state": "start", "data": {}}
state_info = active_states[user_id]
if user_id in active_states:
del active_states[user_id]

# Стало:
context.set_state({"command": "/add", "state": "start", "data": {}})
state_info = context.get_state()
if context.is_active():
context.delete_state()
```

**Handler wrapper'ы** (add_handler.py, edit_handler.py и т.д.):
```python
# Было:
if context.user_id in active_states and active_states[context.user_id].get("command") == "/add":

# Стало:
if context.is_active() and context.command_state == "/add":
```

### 5. Работа с `cancel`

`cancel.py` сейчас удаляет стейт, если он есть. После замены:
```python
if context.is_active():
    context.delete_state()
```

### 6. `bot.py` routing

Убрать `from vk_bot.states import active_states` и заменить проверку `context.user_id in active_states` на `context.is_active()`.

### 7. Тесты

Тесты, которые используют `active_states.clear()` или прямую установку стейта, переходят на мок `ActiveStateStorage` или устанавливают стейт через мокированный `BotContext`.

## Risks / Trade-offs

- **Торговля**: Каждый вызов `get_state()` читает SQLite. Раньше чтение было из памяти. Для VK-бота с < 100 одновременных пользователей это некритично.
- **Риск**: Если база заблокирована, пользователь не сможет продолжить ввод. → Уже есть обработка ошибок в `Database.get_cursor()`, расширять не нужно.
- **Риск**: `UserStateRepository` сейчас создаёт свой `Database()` без shared-подключения. → Исправить, переведя на общий `db` из `Database()` или внедрив зависимость.
