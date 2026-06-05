from typing import Any

from vk_api.utils import get_random_id

from vk_bot.keyboards import main_keyboard

from ..context import BotContext
from .base import AbstractCommandHandler


class StartHandler(AbstractCommandHandler):
    """Handler for the `/start` command."""

    priority = 1000
    commands = ["/start", "start", "начать"]

    def handle(self, context: BotContext) -> Any:
        greeting = (
            "Привет! Я твой персональный трекер чтения и менеджер книг.\n\n"
            "Что я могу сделать:\n"
            "/add - Добавить новую книгу\n"
            "/list - Показать список книг\n"
            "/edit - Редактировать книгу\n"
            "/stats - Статистика чтения\n"
            "/help - Помощь\n\n"
            "Начни с добавления первой книги!"
        )
        context.api.messages.send(
            user_id=context.user_id,
            message=greeting,
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return True
