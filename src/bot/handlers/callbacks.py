"""Обработчики callback-queries для Telegram-бота."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import logger
from bot.handlers.book import progress, status, delete, edit
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

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
            f"Операция отменена"
        )
        await query.message.reply_text(
            "Что вы хотите сделать дальше?",
            reply_markup=keyboards.main_menu()
        )

    elif data[0] == "select_status":
        # Выбор статуса книги
        await status.handle_status_callback(update, context)

    elif data[0] == "change_status":
        # Изменение статуса книги
        await status.handle_status_callback(update, context)

    elif data[0] == "update_progress":
        # Обновление прогресса чтения
        await progress.handle_progress_callback(update, context)

    elif data[0] == "delete_book":
        # Удаление книги
        await delete.handle_delete_callback(update, context)

    elif data[0] == "select_book_for_edit":
        # Редактирование книги
        await edit.handle_edit_callback(update, context)
