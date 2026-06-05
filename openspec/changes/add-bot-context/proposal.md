## Why

Сейчас обработчики команд получают разрозненные параметры — `api`, `user_id`, `text`, `payload` — через `*args` и `**kwargs`. Некоторым хендлерам (например, `/export`) требуется `VkUpload`, который создаётся на месте. Отсутствует единый объект, инкапсулирующий всё необходимое для работы хендлера: API-клиент, загрузчик файлов и данные события. Это усложняет тестирование, делает сигнатуры хендлеров нестабильными и затрудняет добавление новых возможностей (например, доступа к произвольным полям события).

## What Changes

- Введение класса `BotContext`, который объединяет:
  - `vk` — экземпляр `VkApi` (для создания `VkUpload` и других объектов)
  - `upload` — экземпляр `VkUpload` (фабрикуется из `vk`)
  - `event` — исходный объект события VK LongPoll
  - Свойства-хелперы: `text`, `payload`, `user_id`, `peer_id`
- Изменение сигнатуры `handle()` в `AbstractCommandHandler` — вместо разрозненных параметров передаётся `BotContext`
- Обновление `CommandRouter.route()` — принимает `BotContext` вместо россыпи аргументов
- Обновление `VkBookShelfBot.handle_event()` — создаёт `BotContext` один раз и передаёт его в роутер и в fallback-хендлеры
- **BREAKING**: Сигнатура `AbstractCommandHandler.handle()` меняется: `handle(self, context: BotContext) -> Any` вместо `handle(self, *args, **kwargs)`
- **BREAKING**: Сигнатура `CommandRouter.route()` меняется: `route(self, context: BotContext) -> Any` вместо `route(self, command, *args, **kwargs)`
- Все существующие хендлеры (как wrapper-классы, так и legacy-функции) обновляются для работы с `BotContext`

## Capabilities

### New Capabilities
- `bot-context`: Определение класса `BotContext`, его свойств и методов доступа к данным события

### Modified Capabilities

*(Нет изменений в существующих спецификациях)*

## Impact

- `src/vk_bot/bot.py` — создание `BotContext`, передача в роутер и fallback-хендлеры
- `src/vk_bot/command_router.py` — новая сигнатура `route(context)`
- `src/vk_bot/handlers/base.py` — новая сигнатура `AbstractCommandHandler.handle(context)`
- `src/vk_bot/handlers/add_handler.py`, `edit_handler.py`, `list_handler.py`, `details_handler.py` — обновление wrapper-хендлеров
- `src/vk_bot/handlers/add.py`, `edit.py`, `list.py`, `details.py`, `start.py`, `help.py`, `export.py`, `cancel.py`, `stats.py` — обновление logic-функций
- `tests/` — обновление тестов, использующих `FakeVkApiMethod`, под новую сигнатуру
