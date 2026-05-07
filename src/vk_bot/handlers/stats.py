"""Handler for the /stats command in the VK bot."""

from vk_api.vk_api import VkApiMethod
from vk_api.utils import get_random_id

from core.services import BookService
from vk_bot.keyboards import start_keyboard
from vk_bot.user_helpers import get_or_create_user


def handle_stats_command(vk: VkApiMethod, user_id: int) -> None:
    """Send reading statistics for the given VK ``user_id``.

    The statistics are retrieved from :class:`BookService` and formatted
    as a plain‑text message suitable for VK.
    """
    # Ensure we have a user entry in the system.
    user = get_or_create_user(vk, user_id)

    # Retrieve statistics for this user.
    book_service = BookService()
    stats = book_service.get_stats(user.id)

    # Build the response text.
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

    # Send the message via VK API.
    vk.messages.send(
        user_id=user_id,
        message=stats_text,
        keyboard=start_keyboard().get_keyboard(),
        random_id=get_random_id()
    )
