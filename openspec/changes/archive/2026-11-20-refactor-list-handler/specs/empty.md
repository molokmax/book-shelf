## ADDED Requirements

### Requirement: Структура обработчика list

Система SHALL реализовывать команду `/list` целиком в классе `ListHandler` в файле `list_handler.py`, без использования отдельного модуля `list.py`.

#### Scenario: Вся логика внутри ListHandler
- **WHEN** выполняется команда `/list`
- **THEN** `ListHandler.handle()` диспетчеризует обработку по значению `state`
- **THEN** каждый шаг (`choose_filter`, `choose_status`, `choose_tag`) реализован в отдельном методе `ListHandler`
- **THEN** модуль `list.py` отсутствует

#### Scenario: Тесты обновлены
- **WHEN** тесты команды `/list` запускаются
- **THEN** они импортируют `ListHandler` из `vk_bot.handlers.list_handler`
- **THEN** все тесты проходят без изменений логики

## MODIFIED Requirements

<!-- Нет изменений требований на уровне спецификаций -->

## REMOVED Requirements

### Requirement: Модуль list.py

**Reason**: Вся логика перенесена в `list_handler.py`
**Migration**: Импорты `vk_bot.handlers.list` заменить на `vk_bot.handlers.list_handler.ListHandler`