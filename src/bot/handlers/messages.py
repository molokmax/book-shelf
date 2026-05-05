"""Обработчики текстовых сообщений для Telegram-бота."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import logger
from bot.handlers.book import add, progress, edit
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

    if state == "waiting_for_litres_url":
        await add.handle_add_book_from_litres(update, context)
        return

    if state == "waiting_for_litres_tags":
        await add.handle_litres_book_tags(update, context)
        return

    if state == "waiting_for_progress_input":
        await progress.handle_progress_input(update, context)
        return

    # Проверяем, есть ли активный диалог редактирования тэгов
    edit_state = context.user_data.get("edit_state")
    if edit_state == "editing_tags":
        # Проверяем, не является ли сообщение командой отмены
        if update.message.text == "/cancel":
            context.user_data.clear()
            await update.message.reply_text(
                "Редактирование тегов отменено.",
                reply_markup=keyboards.main_menu()
            )
            return
        await edit.handle_edit_tags_message(update, context)
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
