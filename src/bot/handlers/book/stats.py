"""Обработчики команды /stats и связанных с ней сообщений и callback-ов."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import helpers, logger
from core.services import BookService, UserService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /stats."""
    # Получаем или создаём пользователя
    user = helpers.get_or_create_user(update)

    book_service = BookService()
    stats_data = book_service.get_stats(user.id)

    stats_text = (
        "📊 **Статистика чтения**\n\n"
        f"• Всего книг: {stats_data['total_books']}\n"
        f"• Прочитано: {stats_data['read_books']}\n"
        f"• Читаю сейчас: {stats_data['reading_books']}\n"
        f"• Хочу прочитать: {stats_data['want_to_read_books']}\n"
        f"• Отложено: {stats_data['postponed_books']}\n\n"
        f"• Всего страниц: {stats_data['total_pages']}\n"
        f"• Прочитано страниц: {stats_data['read_pages']}\n"
        f"• Средний прогресс: {stats_data['avg_progress']:.1f}%\n"
    )

    await update.message.reply_text(stats_text, parse_mode="Markdown")
