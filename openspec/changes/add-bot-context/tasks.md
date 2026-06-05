## 1. BotContext class

- [x] 1.1 Создать `src/vk_bot/context.py` с классом `BotContext`, конструктором (`vk`, `upload`, `event`) и `__slots__`
- [x] 1.2 Добавить read-only свойства `user_id`, `peer_id`, `text` — делегируют к `event`
- [x] 1.3 Добавить свойство `payload` — парсит `event.payload` как JSON, возвращает `{}` при None/пустой строке
- [x] 1.4 Добавить свойство `command` — извлекает команду из payload["command"] или event.text.lower()

## 2. Обновление AbstractCommandHandler

- [x] 2.1 Изменить сигнатуру `handle(self, context: BotContext) -> Any` в `handlers/base.py`

## 3. Обновление CommandRouter

- [x] 3.1 Изменить сигнатуру `route(self, context: BotContext) -> Any` — извлекать `context.command` для поиска хендлера
- [x] 3.2 Передавать `context` в `handler.handle(context)` вместо распаковки аргументов

## 4. Обновление wrapper-хендлеров

- [x] 4.1 `AddHandler.handle(context)` — извлечь данные из контекста, передать в legacy-функцию
- [x] 4.2 `EditHandler.handle(context)` — аналогично
- [x] 4.3 `ListHandler.handle(context)` — аналогично
- [x] 4.4 `DetailsHandler.handle(context)` — аналогично

## 5. Обновление legacy-функций

- [x] 5.1 `start.py` — добавить параметр `context` (или адаптировать через wrapper)
- [x] 5.2 `help.py` — аналогично
- [x] 5.3 `cancel.py` — аналогично
- [x] 5.4 `stats.py` — аналогично
- [x] 5.5 `export.py` — использовать `context.upload` вместо создания `VkUpload` на месте; использовать `context.peer_id` вместо `chat_id`
- [x] 5.6 `add.py` — добавить параметр `context`
- [x] 5.7 `edit.py` — добавить параметр `context`
- [x] 5.8 `list.py` — добавить параметр `context`
- [x] 5.9 `details.py` — добавить параметр `context`

## 6. Обновление главного цикла бота

- [x] 6.1 В `VkBookShelfBot.__init__` или `create_longpoll` создать `self.upload = VkUpload(self.vk)`
- [x] 6.2 В `handle_event` создать `BotContext(vk=self.vk, upload=self.upload, event=event)` один раз
- [x] 6.3 Передать `context` в `self.router.route(context)` вместо `(command, self.api, ...)`
- [x] 6.4 Передать `context` во все fallback-вызовы legacy-функций

## 7. Обновление тестов

- [x] 7.1 Добавить файл `tests/test_context.py` с тестами на BotContext (конструктор, свойства, payload, command, immutability)
- [x] 7.2 Обновить `test_handler_base.py` — тесты создают `BotContext` с mock-объектами
- [x] 7.3 Обновить `test_command_router.py` — тесты передают `BotContext`
- [x] 7.4 Обновить `tests/handlers/test_edit_handler.py` и другие handler-тесты — использовать `BotContext` с `FakeVkApiMethod`
