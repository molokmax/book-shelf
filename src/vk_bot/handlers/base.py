"""Base classes for VK bot command handlers."""

import abc
from typing import Any, List, Optional

from vk_api.utils import get_random_id

from vk_bot.context import BotContext

FOREIGN_SCENARIO_MESSAGE = "⚠️ Сейчас активна другая операция. Заверши её или нажми «Отмена»."


class AbstractCommandHandler(abc.ABC):
    """Базовый класс для обработчиков команд.

    Каждый обработчик указывает:
    - ``priority`` – целое число, чем выше, тем раньше обрабатывается команда.
    - ``commands`` – список строк команд (например, ``["/add", "add"]``),
      которые способен обработать данный обработчик.
    - ``scenario_command`` – каноническая команда сценария, которая пишется
      в ``state["command"]``; ``None`` у одношаговых команд.
    - ``is_system`` – системная команда, которая работает и при активном
      чужом сценарии (``/start``, ``/cancel``).

    ``handle`` – шаблонный метод: сначала отклоняет команду, если у
    пользователя активен чужой сценарий, затем вызывает ``_handle``.
    """

    priority: int = 0
    commands: List[str] = []
    scenario_command: Optional[str] = None
    is_system: bool = False

    def can_handle(self, command: str) -> bool:
        """Проверяет, может ли обработчик обработать команду."""
        return command in self.commands

    def handle(self, context: BotContext) -> Any:
        """Обрабатывает команду, не перехватывая чужой сценарий."""
        if context.is_active() and not self.is_system:
            owner = context.get_state().get("command")
            if owner and owner != self.scenario_command:
                self.reject_foreign_scenario(context)
                return True
        return self._handle(context)

    def reject_foreign_scenario(self, context: BotContext) -> None:
        """Сообщает, что активна другая операция.

        Отправляем напрямую через API, без ``context.send_message``: иначе
        цепочка промежуточных сообщений удалит текущий промпт сценария,
        и активный сценарий останется без вопроса.
        """
        context.api.messages.send(
            user_id=context.user_id,
            message=FOREIGN_SCENARIO_MESSAGE,
            random_id=get_random_id(),
        )

    @abc.abstractmethod
    def _handle(self, context: BotContext) -> Any:
        """Обрабатывает команду, используя переданный ``BotContext``."""
        raise NotImplementedError
