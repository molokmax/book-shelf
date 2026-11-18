from typing import Any

from vk_bot.keyboards import main_keyboard

from ..context import BotContext
from .base import AbstractCommandHandler


class StartHandler(AbstractCommandHandler):
    """Handler for the `/start` command.

    Системная команда: работает и при активном чужом сценарии, сбрасывая
    его состояние.
    """

    priority = 1000
    commands = ["/start", "start", "начать"]
    is_system = True

    def _handle(self, context: BotContext) -> Any:
        greeting = (
            "Привет! Я твой персональный трекер чтения и менеджер книг.\n\n"
            "Что я могу сделать:\n"
            "/add - Добавить новую книгу\n"
            "/progress - Обновить прогресс чтения\n"
            "/list - Показать список книг\n"
            "/details - Детали книги\n"
            "/help - Помощь\n\n"
            "Остальные команды доступны через кнопку «Ещё».\n\n"
            "Начни с добавления первой книги!"
        )
        # Приветствие отправляем до delete_state: send_message удалит
        # висящий промпт предыдущего сценария.
        context.send_message(greeting, keyboard=main_keyboard())
        if context.is_active():
            context.delete_state()
        return True
