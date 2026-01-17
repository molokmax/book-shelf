"""Обработчики текстовых сообщений для Telegram-бота."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import logger
from bot.handlers.book import add, progress, priority
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""

    # Проверяем, есть ли активный диалог добавления книги
    state = context.user_data.get("state")
    if state == "waiting_for_title":
        await add.handle_add_book_title(update, context)
        return

    if state == "waiting_for_author":
        await add.handle_add_book_author(update, context)
        return

    if state == "waiting_for_tags":
        await add.handle_add_book_tags(update, context)
        return

    if state == "waiting_for_pages":
        await add.handle_add_book_pages(update, context)
        return

    if state == "waiting_for_priority_change":
        await priority.handle_priority_book_selection(update, context)
        return

    if state == "waiting_for_new_priority":
        # Новый приоритет выбирается через callback
        return

    if state == "waiting_for_progress_input":
        await progress.handle_progress_input(update, context)
        return

    # Если нет активного диалога, показываем помощь
    await update.message.reply_text(
        "Я не понял ваше сообщение. Используйте команды:\n\n"
        "/start - Начало работы\n"
        "/help - Помощь\n"
        "/add - Добавить книгу\n"
        "/list - Показать список книг",
        reply_markup=keyboards.main_menu()
    )
