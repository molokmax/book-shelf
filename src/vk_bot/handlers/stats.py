"""Stats command handler as AbstractCommandHandler subclass.

Содержит полную реализацию команды /stats.
"""

from typing import Any

from vk_api.utils import get_random_id

from core.services import BookService
from vk_bot.keyboards import main_keyboard
from vk_bot.user_helpers import get_or_create_user

from ..context import BotContext
from .base import AbstractCommandHandler


class StatsHandler(AbstractCommandHandler):
    """Handler for the `/stats` command.

    Отображает статистику чтения пользователя.
    """

    priority = 10
    commands = ["/stats", "stats"]

    def handle(self, context: BotContext) -> Any:
        api = context.api
        user_id = context.user_id
        user = get_or_create_user(api, user_id)

        book_service = BookService()
        stats = book_service.get_stats(user.id)

        stats_text = (
            "📊 Статистика чтения\n\n"
            f"Всего книг: {stats['total_books']}\n"
            f"Прочитано: {stats['read_books']}\n"
            f"Читаю сейчас: {stats['reading_books']}\n"
            f"Хочу прочитать: {stats['want_to_read_books']}\n"
            f"Отложено: {stats['postponed_books']}\n\n"
            f"Всего страниц: {stats['total_pages']}\n"
            f"Прочитано страниц: {stats['read_pages']}\n"
            f"Средний прогресс: {stats['avg_progress']:.1f}%"
        )

        api.messages.send(
            user_id=user_id,
            message=stats_text,
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return True
