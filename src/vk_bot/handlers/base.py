"""Base classes for VK bot command handlers."""

import abc
from typing import List


class AbstractCommandHandler(abc.ABC):
    """Базовый класс для обработчиков команд.

    Каждый обработчик указывает:
    - ``priority`` – целое число, чем выше, тем ранже обрабатывается команда.
    - ``commands`` – список строк команд (например, ``["/add", "add"]``),
      которые способен обработать данный обработчик.

    ``can_handle`` проверяет, есть ли запрошенная команда в списке.
    Реализуйте метод ``handle`` в наследниках, принимая любые нужные параметры.
    """

    priority: int = 0
    commands: List[str] = []

    def can_handle(self, command: str) -> bool:
        """Возвращает ``True``, если обработчик может обработать ``command``."""
        return command in self.commands

    @abc.abstractmethod
    def handle(self, *args, **kwargs):
        """Обрабатывает команду.

        Конкретные параметры зависят от реализации обработчика.
        """
        raise NotImplementedError
