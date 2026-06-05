import logging
from typing import List, Dict, Callable, Any

from utils import logger
from utils.config import load_config

from .handlers.base import AbstractCommandHandler


class CommandRouter:
    """Класс роутера команд.

    Хранит список обработчиков, каждый из которых указывает приоритет и список команд, которые он может обработать.
    При получении команды роутер выбирает обработчик с наибольшим приоритетом, у которого ``can_handle`` возвращает ``True``.
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

        Обработчики сортируются по убыванию приоритета, чтобы более «важные» обрабатывали команды первыми.
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
    def route(self, command: str, *args: Any, **kwargs: Any) -> Any:
        """Маршрутизует полученную команду к подходящему обработчику.

        Возвращает результат вызова ``handle`` первого подходящего обработчика.
        Если ни один обработчик не подходит – возвращает ``None``.
        """
        for handler in self.handlers:
            try:
                if handler.can_handle(command):
                    self.logger.debug(
                        "Routing command %s to %s", command, handler.__class__.__name__
                    )
                    return handler.handle(command, *args, **kwargs)
            except Exception as e:
                self.logger.error(
                    "Error in handler %s while processing %s: %s",
                    handler.__class__.__name__,
                    command,
                    e,
                )
        self.logger.warning("No handler found for command %s", command)
        return None
