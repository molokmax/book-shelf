"""Обработчики редактирования книги."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils import logger
from utils import helpers
from utils.helpers import get_or_create_user
from core.services import BookService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /edit - начало редактирования книги."""
    user = get_or_create_user(update)

    book_service = BookService()
    books = book_service.get_all_books(user.id)
    books = helpers.sort_books_by_status(books)

    if not books:
        await update.message.reply_text(
            "У вас нет книг в библиотеке. Сначала добавьте книгу с помощью /add",
            reply_markup=keyboards.main_menu()
        )
        return

    # Создаём клавиатуру с книгами
    keyboard = []
    for book in books:
        keyboard.append([
            InlineKeyboardButton(
                f"{book.title} - {book.author}",
                callback_data=f"select_book_for_edit:{book.id}"
            )
        ])

    await update.message.reply_text(
        "Выберите книгу, которую хотите отредактировать:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # Сохраняем состояние
    context.user_data["edit_state"] = "selecting_book"
    context.user_data["selected_book_id"] = None

async def handle_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback для редактирования книги."""
    query = update.callback_query

    data = query.data.split(":")
    if data[0] == "select_book_for_edit":
        # Пользователь выбрал книгу
        book_id = data[1]
        context.user_data["selected_book_id"] = book_id

        # Создаём клавиатуру с действиями
        keyboard = keyboards.book_actions_keyboard(book_id)

        await query.edit_message_text(
            "Выберите действие для книги:",
            reply_markup=keyboard
        )

        context.user_data["edit_state"] = "selecting_action"
