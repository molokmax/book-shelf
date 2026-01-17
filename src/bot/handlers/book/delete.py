"""Обработчики удаления книги и связанных callback-ов."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import logger
from core.services import BookService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def handle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback для удаления книги."""
    query = update.callback_query

    data = query.data.split(":")
    if data[0] == "delete_book":
        # Удаление книги
        try:
            book_id = data[1]

            book_service = BookService()
            book = book_service.delete_book(book_id)
            
            await query.edit_message_text(
                f"🗑️ Книга '{book.title}' удалена из библиотеки"
            )
            await query.message.reply_text(
                "Что вы хотите сделать дальше?",
                reply_markup=keyboards.main_menu()
            )
        except Exception as e:
            log.error(f"Ошибка при удалении книги: {e}")
            await query.edit_message_text("❌ Произошла ошибка при удалении книги")
