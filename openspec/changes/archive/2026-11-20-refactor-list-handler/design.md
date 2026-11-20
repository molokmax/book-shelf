## Context

Сейчас `list_handler.py` — тонкая обёртка, импортирующая функции из `list.py`. Пользователь хочет перенести всю логику внутрь `ListHandler`, разбив на отдельные методы по состояниям, и удалить `list.py`. Это отличается от подхода `add.py`/`edit.py`, где логика остаётся в отдельном файле; здесь принято решение консолидировать.

## Goals / Non-Goals

**Goals:**
- Перенести всю реализацию из `list.py` в `list_handler.py` как методы `ListHandler`
- Каждое значение `state` → отдельный метод класса
- `ListHandler.handle()` диспетчеризует по `state`
- Удалить `list.py`
- Обновить тесты

**Non-Goals:**
- Изменение логики фильтрации, отображения или форматов сообщений
- Изменение регистрации в `bot.py` (класс `ListHandler` остаётся, только его содержимое меняется)
- Изменение других команд или модулей

## Decisions

- **Куда поместить `_finish`**: сделать приватным методом `ListHandler._finish(self, message, keyboard=None)`. Доступен всем методам обработки.
- **Имена методов**: `_handle_choose_filter`, `_handle_choose_status`, `_handle_choose_tag`, а также новый `_handle_entry` (вместо `handle_list_command`). `handle()` диспетчеризует:

  ```python
  def handle(self, context: BotContext) -> Any:
      if context.is_active() and context.command_state == "/list":
          state = context.get_state()["state"]
          method = getattr(self, f"_handle_{state}")
          return method(context)
      else:
          return self._handle_entry(context)
  ```

- **Тесты**: вместо импорта `vl_bot.handlers.list` → импортировать `ListHandler` из `vk_bot.handlers.list_handler` и вызывать `handler.handle(context)`.

## Risks / Trade-offs

- **Риск регрессии** → Тесты проверяют поведение, а не структуру. При корректном переносе все тесты пройдут. Запустить `pytest` целиком после изменений.
- **Несоответствие паттерну add/edit** → Осознанное решение пользователя. `list_handler` станет самодостаточным, без отдельного `list.py`.