"""Обработчики изменения статуса книги и связанных callback-ов."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import logger
from utils.helpers import get_status_name
from core.services import BookService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def handle_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback для изменения статуса книги."""
    query = update.callback_query

    data = query.data.split(":")
    if data[0] == "select_status":
        # Пользователь выбрал изменение статуса - показываем клавиатуру с вариантами
        book_id = data[1]

        await query.edit_message_text(
            "Выберите новый статус для книги:",
            reply_markup=keyboards.status_keyboard(book_id)
        )
    elif data[0] == "change_status":
        # Изменение статуса книги
        try:
            book_id = data[1]
            new_status = data[2]

            book_service = BookService()
            book = book_service.update_book_status(book_id, new_status)

            await query.edit_message_text(
                f"✅ Статус книги '{book.title}' изменён на '{get_status_name(book.status)}'"
            )
            await query.message.reply_text(
                "Что вы хотите сделать дальше?",
                reply_markup=keyboards.main_menu()
            )
        except Exception as e:
            log.error(f"Ошибка при изменении статуса: {e}")
            await query.edit_message_text("❌ Произошла ошибка при изменении статуса")
