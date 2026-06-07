from typing import Any, List

from utils import logger
from utils.config import load_config

from .context import BotContext
from .handlers.base import AbstractCommandHandler


class CommandRouter:
    """Класс роутера команд.

    Хранит список обработчиков с приоритетом и списком команд.
    При получении команды выбирает обработчик с наибольшим приоритетом,
    у которого ``can_handle`` возвращает ``True``.
    """

    def __init__(self) -> None:
        self.handlers: List[AbstractCommandHandler] = []
        self.logger = logger.setup_logger(__name__)
        self.config = load_config()

    # ---------------------------------------------------------------------
    # Регистрация обработчиков
    # ---------------------------------------------------------------------
    def register_handler(self, handler: AbstractCommandHandler) -> None:
        """Регистрирует обработчик.

        Обработчики сортируются по убыванию приоритета.
        """
        self.handlers.append(handler)
        # Сортируем каждый раз – количество обработчиков небольшое
        self.handlers.sort(key=lambda h: getattr(h, "priority", 0), reverse=True)
        self.logger.debug(
            "Handler %s registered with priority %s",
            handler.__class__.__name__,
            getattr(handler, "priority", 0),
        )

    # ---------------------------------------------------------------------
    # Основной роутинг
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # Поиск обработчика по команде
    # ---------------------------------------------------------------------
    def _find_handler(self, command: str, context: BotContext) -> Any:
        """Пытается найти обработчик для указанной команды.

        Возвращает результат ``handle()`` первого подходящего обработчика
        или ``None``, если ни один не подошёл.
        """
        for handler in self.handlers:
            try:
                if handler.can_handle(command):
                    self.logger.debug(
                        "Routing command %s to %s",
                        command,
                        handler.__class__.__name__,
                    )
                    return handler.handle(context)
            except Exception as e:
                self.logger.error(
                    "Error in handler %s while processing %s: %s",
                    handler.__class__.__name__,
                    command,
                    e,
                )
        return None

    # ---------------------------------------------------------------------
    # Основной роутинг
    # ---------------------------------------------------------------------
    def route(self, context: BotContext) -> Any:
        """Маршрутизует команду из ``context`` к подходящему обработчику.

        Сначала пытается найти обработчик по ``context.command``.
        Если ни один не подошёл и у пользователя есть активный стейт,
        выполняет второй проход по обработчикам с ``context.command_state``.

        Возвращает результат вызова ``handle`` первого подходящего обработчика,
        иначе ``None``.
        """
        command = context.command

        result = self._find_handler(command, context)
        if result is not None:
            return result

        if context.is_active():
            state_command = context.command_state
            if state_command:
                self.logger.debug(
                    "No handler matched command '%s', " "trying state command '%s'",
                    command,
                    state_command,
                )
                result = self._find_handler(state_command, context)
                if result is not None:
                    return result

        self.logger.warning("No handler found for command %s", command)
        return None
