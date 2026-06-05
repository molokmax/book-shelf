"""Base classes for VK bot command handlers."""

import abc
from typing import Any, List

from vk_bot.context import BotContext


class AbstractCommandHandler(abc.ABC):
    """Базовый класс для обработчиков команд.

    Каждый обработчик указывает:
    - ``priority`` – целое число, чем выше, тем раньше обрабатывается команда.
    - ``commands`` – список строк команд (например, ``["/add", "add"]``),
      которые способен обработать данный обработчик.

    ``can_handle`` проверяет, есть ли запрошенная команда в списке.
    Реализуйте метод ``handle`` в наследниках.
    """

    priority: int = 0
    commands: List[str] = []

    def can_handle(self, command: str) -> bool:
        """Возвращает ``True``, если обработчик может обработать ``command``."""
        return command in self.commands

    @abc.abstractmethod
    def handle(self, context: BotContext) -> Any:
        """Обрабатывает команду, используя переданный ``BotContext``."""
        raise NotImplementedError
