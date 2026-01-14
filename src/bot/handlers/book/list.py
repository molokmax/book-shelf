"""Обработчики команды /list и связанных с ней сообщений и callback-ов."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import helpers, logger
from core.services import BookService

log = logger.setup_logger(__name__)

async def list_books_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /list."""
    user = helpers.get_or_create_user(update)

    book_service = BookService()
    books = book_service.get_all_books(user.id)

    if not books:
        await update.message.reply_text("Ваша библиотека пуста. Добавьте первую книгу с помощью /add")
        return

    response = "📚 Ваша библиотека:\n\n"
    for i, book in enumerate(books, 1):
        status_emoji = {
            "want_to_read": "📖",
            "reading": "📚",
            "read": "📕",
            "postponed": "⏸️"
        }.get(book.status, "📘")

        priority_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }.get(book.priority, "⚪")

        tags_text = ", ".join(book.tags) if book.tags else "Нет тегов"
        response += (
            f"{i}. {status_emoji} {priority_emoji} **{book.title}**\n"
            f"   *Автор:* {book.author}\n"
            f"   *Теги:* {tags_text}\n"
            f"   *Страниц:* {book.pages}\n"
            f"   *Прогресс:* {book.progress}%\n\n"
        )

    await update.message.reply_text(response, parse_mode="Markdown")
