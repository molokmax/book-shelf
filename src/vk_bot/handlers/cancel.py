from typing import Any

from vk_api.utils import get_random_id

from vk_bot.keyboards import main_keyboard

from ..context import BotContext
from .base import AbstractCommandHandler


class CancelHandler(AbstractCommandHandler):

    priority = 100
    commands = ["/cancel", "cancel", "отмена"]

    def handle(self, context: BotContext) -> Any:
        user_id = context.user_id
        if context.is_active():
            context.delete_state()

        context.api.messages.send(
            user_id=user_id,
            message="Операция отменена",
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return True
