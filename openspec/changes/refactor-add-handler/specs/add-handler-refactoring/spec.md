## ADDED Requirements

### Requirement: AddHandler содержит всю логику команды /add
`AddHandler` SHALL содержать все методы обработки команды `/add`. Файл `add.py` SHALL быть удалён.

#### Scenario: handle() вызывает _handle_start если нет активного стейта
- **WHEN** `AddHandler.handle()` вызывается с контекстом без активного стейта
- **THEN** вызывается метод `_handle_start`

#### Scenario: handle() вызывает _handle_step если есть активный стейт
- **WHEN** `AddHandler.handle()` вызывается с контекстом с активным стейтом для команды `/add`
- **THEN** вызывается метод `_handle_step`

### Requirement: Каждый шаг стейт-машины — отдельный метод
Каждое состояние (`choose_method`, `waiting_for_title`, `waiting_for_author`, `waiting_for_pages`, `waiting_for_link`, `waiting_for_tags`, `waiting_for_litres_url`, `waiting_for_litres_confirm`, `waiting_for_litres_tags`) SHALL обрабатываться отдельным приватным методом класса `AddHandler`.

#### Scenario: _handle_step диспетчеризует по state через словарь
- **WHEN** `_handle_step` получает контекст с `state == "choose_method"`
- **THEN** вызывается метод, соответствующий этому состоянию (например, `_handle_choose_method`)

#### Scenario: Неизвестный state сбрасывает стейт
- **WHEN** `_handle_step` получает контекст с неизвестным `state`
- **THEN** стейт пользователя удаляется и отправляется сообщение о сбросе

### Requirement: Клавиатуры определены внутри add_handler.py
Все функции-клавиатуры, специфичные для команды `/add`, SHALL быть определены в `add_handler.py`.

#### Scenario: Клавиатуры доступны как статические методы AddHandler
- **WHEN** метод `AddHandler.create_add_method_keyboard()` вызывается
- **THEN** возвращается `VkKeyboard` с кнопками "Ручное", "Из LitRes", "Отмена"
