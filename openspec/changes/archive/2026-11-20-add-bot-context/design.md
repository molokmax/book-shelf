## Context

Сейчас каждый хендлер получает параметры через разрозненные `*args` и `**kwargs`: `api`, `user_id`, `text`, `payload`. Сигнатуры нестабильны — `/export` дополнительно требует `upload` и `chat_id`, а остальные хендлеры не имеют доступа к `VkUpload` и полному объекту события. `BotContext` решает эту проблему, предоставляя единый контейнер со всем необходимым.

## Goals / Non-Goals

**Goals:**
- Единый `BotContext` с `vk`, `upload`, `event` и удобными свойствами (`text`, `payload`, `user_id`, `peer_id`, `command`)
- Новая сигнатура `AbstractCommandHandler.handle(context: BotContext)`
- Новая сигнатура `CommandRouter.route(context: BotContext)`
- Создание `BotContext` один раз в `bot.py` и передача по цепочке
- Обновление всех существующих хендлеров (wrapper-классы + legacy-функции)
- Обновление тестов

**Non-Goals:**
- Рефакторинг системы состояний (in-memory `active_states` / SQLite `UserStateRepository`)
- Изменение бизнес-логики в `src/core/`
- Добавление новых команд или функциональности

## Decisions

### 1. Формат класса: `dataclass(frozen=True)` + вычисляемые свойства
`BotContext` будет обычным классом с `@property` для вычисляемых полей. Три хранимых атрибута (`vk`, `upload`, `event`) устанавливаются в `__init__`, остальные (`user_id`, `peer_id`, `text`, `payload`, `command`) — вычисляемые свойства.

**Альтернативы:**
- `NamedTuple` — иммутабельно, но нельзя добавить методы без переопределения
- `dataclass(frozen=True)` — близко, но вычисляемые свойства не укладываются в концепцию поля
- Простой `@dataclass` — теряем контроль над иммутабельностью

### 2. Расположение: `src/vk_bot/context.py`
Новый файл, т.к. `BotContext` — концепция только VK-слоя, не core.

### 3. Создание VkUpload: один раз в bot.py
`VkUpload(self.vk)` будет создаваться сразу после инициализации `VkApi` и передаваться в `BotContext`. Это избавляет от ленивого создания в `/export`.

### 4. Стратегия миграции хендлеров
- Сначала обновляется `AbstractCommandHandler.handle(context)`, что ломает все wrapper-классы
- Затем обновляются wrapper-классы: они получают `BotContext` и передают данные в legacy-функции
- Legacy-функции получают отдельный `BotContext`-параметр (или адаптируются через враппер)
- `CommandRouter.route(context)` извлекает `context.command` для `can_handle()`

### 5. Тестирование
В тестах будет создаваться `BotContext` с mock-объектами для `vk`, `upload`, `event`. `FakeVkApiMethod` переиспользуется, но теперь передаётся внутри `BotContext`.

## Risks / Trade-offs

- **[R] Обратная совместимость**: Меняются сигнатуры `handle()` и `route()` — все внешние интеграции и тесты потребуют обновления
  → **Mitigation**: Одновременное обновление всех хендлеров и тестов в рамках одного коммита

- **[R] Legacy-функции**: Функции вроде `handle_start_command(vk, user_id)` не используют `BotContext` напрямую
  → **Mitigation**: Wrapper-классы распаковывают `BotContext` и передают нужные аргументы в legacy-функции. Постепенно legacy-функции можно рефакторить

- **[R] Размер объекта**: `BotContext` содержит ссылки на тяжёлые объекты (`VkApi`, событие)
  → **Mitigation**: Ссылки лёгкие, аллокация одноразовая за событие. Никакого влияния на память
