"""Обработчик команды просмотра достижений пользователя."""

from typing import Any

from core.services import AchievementService
from utils import helpers, logger
from vk_bot.keyboards import main_keyboard
from vk_bot.user_helpers import get_or_create_user

from ..context import BotContext
from .base import AbstractCommandHandler

log = logger.setup_logger(__name__)


class AchievementsHandler(AbstractCommandHandler):
    """Показывает полный каталог и ретроспективно выдаёт заслуженные награды."""

    priority = 10
    commands = ["/achievements"]

    def _handle(self, context: BotContext) -> Any:
        user = get_or_create_user(context.api, context.user_id)
        try:
            result = AchievementService().check(user.id)
        except Exception as error:
            log.error("Failed to load achievements for user %s: %s", user.id, error)
            context.send_message(
                helpers.format_invalid_input("Попробуй открыть каталог ещё раз позже."),
                keyboard=main_keyboard(),
            )
            return True

        parts = [
            helpers.format_new_achievements(result.new_achievements),
            helpers.format_achievement_catalog(result.statuses),
        ]
        context.send_message(
            "\n\n".join(part for part in parts if part),
            keyboard=main_keyboard(),
        )
        return True
