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

    elif data[0] == "edit_tags":
        # Пользователь выбрал изменение тэгов
        book_id = data[1]
        book_service = BookService()
        book = book_service.get_book_by_id(book_id)

        if not book:
            await query.edit_message_text("Книга не найдена")
            return

        # Показываем текущие тэги
        tags_text = ", ".join(book.tags) if book.tags else "Нет тэгов"
        await query.edit_message_text(
            f"Текущие тэги книги:\n{tags_text}\n\n"
            f"Отправьте новые тэги через запятую (например: фантастика, наука, приключения).\n"
            f"Или нажмите кнопку отмены ниже.",
            reply_markup=keyboards.cancel_inline_keyboard()
        )

        # Сохраняем состояние
        context.user_data["edit_state"] = "editing_tags"
        context.user_data["selected_book_id"] = book_id

async def handle_edit_tags_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик сообщения с новыми тэгами для книги."""
    if context.user_data.get("edit_state") != "editing_tags":
        return

    message_text = update.message.text.strip()

    book_id = context.user_data.get("selected_book_id")
    if not book_id:
        await update.message.reply_text("Ошибка: книга не выбрана")
        return

    book_service = BookService()
    book = book_service.get_book_by_id(book_id)

    if not book:
        await update.message.reply_text("Книга не найдена")
        return

    # Парсим тэги
    tags = [tag.strip() for tag in message_text.split(",") if tag.strip()]

    # Обновляем тэги
    updated_book = book_service.update_book_tags(book_id, tags)

    # Форматируем новые тэги для отображения
    new_tags_text = ", ".join(updated_book.tags) if updated_book.tags else "Нет тэгов"

    await update.message.reply_text(
        f"Тэги книги успешно обновлены!\n\n"
        f"Новые тэги: {new_tags_text}\n\n"
        f"Что вы хотите сделать дальше?",
        reply_markup=keyboards.main_menu()
    )

    # Сбрасываем состояние
    context.user_data.clear()
