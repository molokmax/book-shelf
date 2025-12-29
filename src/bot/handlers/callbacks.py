"""Обработчики callback-queries для Telegram-бота."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.services import BookService
from bot.keyboards import main as keyboards

logger = logging.getLogger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback-queries."""
    query = update.callback_query
    await query.answer()

    if not query.data:
        return

    data = query.data.split(":")

    if data[0] == "cancel":
        # Отмена текущей операции
        context.user_data.clear()
        await query.edit_message_text(
            "Операция отменена.\n\nЧто вы хотите сделать дальше?",
            reply_markup=keyboards.main_menu()
        )

    elif data[0] == "change_status":
        # Изменение статуса книги
        try:
            book_id = int(data[1])
            new_status = data[2]

            book_service = BookService()
            book = book_service.update_book_status(book_id, new_status)

            await query.edit_message_text(
                f"✅ Статус книги '{book.title}' изменён на '{book.status}'",
                reply_markup=keyboards.main_menu()
            )
        except Exception as e:
            logger.error(f"Ошибка при изменении статуса: {e}")
            await query.edit_message_text("❌ Произошла ошибка при изменении статуса")

    elif data[0] == "change_priority":
        # Изменение приоритета книги
        try:
            book_id = int(data[1])
            new_priority = data[2]

            book_service = BookService()
            book = book_service.update_book_priority(book_id, new_priority)

            await query.edit_message_text(
                f"✅ Приоритет книги '{book.title}' изменён на '{book.priority}'",
                reply_markup=keyboards.main_menu()
            )
        except Exception as e:
            logger.error(f"Ошибка при изменении приоритета: {e}")
            await query.edit_message_text("❌ Произошла ошибка при изменении приоритета")

    elif data[0] == "update_progress":
        # Обновление прогресса чтения
        try:
            book_id = int(data[1])
            new_progress = int(data[2])

            book_service = BookService()
            book = book_service.update_book_progress(book_id, new_progress)

            await query.edit_message_text(
                f"✅ Прогресс чтения книги '{book.title}' обновлён до {book.progress}%",
                reply_markup=keyboards.main_menu()
            )
        except Exception as e:
            logger.error(f"Ошибка при обновлении прогресса: {e}")
            await query.edit_message_text("❌ Произошла ошибка при обновлении прогресса")

    elif data[0] == "delete_book":
        # Удаление книги
        try:
            book_id = int(data[1])

            book_service = BookService()
            book = book_service.delete_book(book_id)

            await query.edit_message_text(
                f"🗑️ Книга '{book.title}' удалена из библиотеки",
                reply_markup=keyboards.main_menu()
            )
        except Exception as e:
            logger.error(f"Ошибка при удалении книги: {e}")
            await query.edit_message_text("❌ Произошла ошибка при удалении книги")
