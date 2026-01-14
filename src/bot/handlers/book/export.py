"""Обработчики команды /export и связанных с ней сообщений и callback-ов."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import helpers, logger
from core.services import BookService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /export."""
    user = helpers.get_or_create_user(update)

    book_service = BookService()
    export_data = book_service.export_library(user.id)

    await update.message.reply_text(
        "📥 Экспорт библиотеки завершён!\n\n"
        "Данные сохранены в файл. Вы можете загрузить его или использовать для резервного копирования.",
        reply_markup=keyboards.main_menu()
    )
