from typing import Any

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
            "/progress - Обновить прогресс чтения\n"
            "/list - Показать список книг\n"
            "/edit - Редактировать книгу\n"
            "/stats - Статистика чтения\n"
            "/help - Помощь\n\n"
            "Начни с добавления первой книги!"
        )
        context.send_message(greeting, keyboard=main_keyboard())
        return True
