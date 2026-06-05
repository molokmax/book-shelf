## ADDED Requirements

### Requirement: StartHandler обрабатывает команду /start
Система SHALL обрабатывать команду `/start` через `StartHandler`, наследующий `AbstractCommandHandler`.

#### Scenario: Пользователь отправляет /start
- **WHEN** пользователь отправляет сообщение `/start`
- **THEN** `CommandRouter` направляет команду в `StartHandler`
- **THEN** `StartHandler.handle()` отправляет приветственное сообщение с главной клавиатурой

#### Scenario: Пользователь отправляет "начать"
- **WHEN** пользователь отправляет сообщение `начать`
- **THEN** `CommandRouter` направляет команду в `StartHandler`
- **THEN** `StartHandler.handle()` отправляет приветственное сообщение с главной клавиатурой

### Requirement: StartHandler имеет наивысший приоритет
Система SHALL гарантировать, что `StartHandler` обрабатывается раньше всех остальных обработчиков.

#### Scenario: Приоритет 1000
- **WHEN** `CommandRouter` сортирует обработчики
- **THEN** `StartHandler.priority` SHALL быть больше, чем у любого другого зарегистрированного обработчика (например, 1000)
- **THEN** `StartHandler` SHALL быть первым в списке обработчиков после сортировки по убыванию приоритета

### Requirement: Старая реализация удалена
Система SHALL NOT содержать старую реализацию обработки `/start`.

#### Scenario: Нет ручной обработки в handle_event
- **WHEN** `VkBookShelfBot.handle_event()` получает команду `/start`
- **THEN** обработка SHALL происходить только через `CommandRouter`
- **THEN** в `handle_event()` SHALL NOT быть отдельного `if command == "/start"` блока

#### Scenario: Файл start.py удалён
- **WHEN** проверяется кодовая база
- **THEN** файл `src/vk_bot/handlers/start.py` SHALL NOT существовать
