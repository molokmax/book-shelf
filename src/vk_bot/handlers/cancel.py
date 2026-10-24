from typing import Any

from vk_bot.keyboards import main_keyboard

from ..context import BotContext
from .base import AbstractCommandHandler


class CancelHandler(AbstractCommandHandler):

    priority = 100
    commands = ["/cancel", "cancel", "отмена"]

    def handle(self, context: BotContext) -> Any:
        # Финальное сообщение отправляем до delete_state: send_message удалит
        # последний промпт, а id финала стёрется вместе со стейтом и не будет
        # удалён следующими сообщениями.
        context.send_message("Операция отменена", keyboard=main_keyboard())
        if context.is_active():
            context.delete_state()
        return True
