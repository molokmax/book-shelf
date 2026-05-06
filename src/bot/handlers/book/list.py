"""Обработчики команды /list и связанных с ней сообщений и callback-ов."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import helpers, tg_helpers, logger
from core.services import BookService

log = logger.setup_logger(__name__)

async def list_books_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /list."""
    user = tg_helpers.get_or_create_user(update)

    book_service = BookService()
    books = book_service.get_all_books(user.id)
    books = helpers.sort_books_by_status(books)

    if not books:
        await update.message.reply_text("Ваша библиотека пуста. Добавьте первую книгу с помощью /add")
        return

    response = "📚 Ваша библиотека:\n\n"
    for i, book in enumerate(books, 1):
        response += helpers.format_book_info(i, book) + "\n"

    await update.message.reply_text(response, parse_mode="Markdown")
