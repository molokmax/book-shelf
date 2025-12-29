"""Обработчики текстовых сообщений для Telegram-бота."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from core.services import BookService
from bot.keyboards import main as keyboards

logger = logging.getLogger(__name__)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    text = update.message.text.strip()

    # Проверяем, есть ли активный диалог добавления книги
    state = context.user_data.get("state")
    if state == "waiting_for_title":
        # Сохраняем название книги
        context.user_data["book_title"] = text
        await update.message.reply_text(
            "Отлично! Теперь введите автора книги:",
            reply_markup=keyboards.cancel_keyboard()
        )
        context.user_data["state"] = "waiting_for_author"
        return

    if state == "waiting_for_author":
        # Сохраняем автора
        context.user_data["book_author"] = text
        await update.message.reply_text(
            "Хорошо! Теперь введите жанр книги (например: Фантастика, Детектив):",
            reply_markup=keyboards.cancel_keyboard()
        )
        context.user_data["state"] = "waiting_for_genre"
        return

    if state == "waiting_for_genre":
        # Сохраняем жанр
        context.user_data["book_genre"] = text
        await update.message.reply_text(
            "Отлично! Теперь введите количество страниц в книге:",
            reply_markup=keyboards.cancel_keyboard()
        )
        context.user_data["state"] = "waiting_for_pages"
        return

    if state == "waiting_for_pages":
        # Сохраняем количество страниц и создаём книгу
        try:
            pages = int(text)
            if pages <= 0:
                raise ValueError

            book_service = BookService()
            book = book_service.create_book(
                title=context.user_data["book_title"],
                author=context.user_data["book_author"],
                genre=context.user_data["book_genre"],
                pages=pages
            )

            # Очищаем состояние
            context.user_data.clear()

            await update.message.reply_text(
                f"✅ Книга '{book.title}' успешно добавлена в вашу библиотеку!\n\n"
                "Вы можете:\n"
                "/list - Посмотреть все книги\n"
                "/add - Добавить ещё одну книгу",
                reply_markup=keyboards.main_menu()
            )

        except ValueError:
            await update.message.reply_text(
                "❌ Некорректное количество страниц. Пожалуйста, введите число.",
                reply_markup=keyboards.cancel_keyboard()
            )
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
