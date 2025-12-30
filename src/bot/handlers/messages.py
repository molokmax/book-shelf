"""Обработчики текстовых сообщений для Telegram-бота."""
\
from telegram import Update
from telegram.ext import ContextTypes

from utils import logger
from core.services import BookService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

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
            "Хорошо! Теперь введите теги книги через запятую (например: Tech, Программирование):",
            reply_markup=keyboards.cancel_keyboard()
        )
        context.user_data["state"] = "waiting_for_tags"
        return

    if state == "waiting_for_tags":
        # Сохраняем теги
        context.user_data["book_tags"] = [tag.strip() for tag in text.split(",") if tag.strip()]
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
                tags=context.user_data["book_tags"],
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
