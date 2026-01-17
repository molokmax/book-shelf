"""Обработчики команды /priority и связанных с ней сообщений и callback-ов."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import helpers, logger
from core.services import BookService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def change_priority_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /priority."""
    user = helpers.get_or_create_user(update)

    book_service = BookService()
    books = book_service.get_all_books(user.id)

    if not books:
        await update.message.reply_text("Ваша библиотека пуста. Добавьте первую книгу с помощью /add")
        return

    # Показываем список книг с их текущим приоритетом
    response = "🎯 Выберите книгу для изменения приоритета:\n\n"
    for i, book in enumerate(books, 1):
        status_emoji = {
            "want_to_read": "📖",
            "reading": "📚",
            "read": "📕",
            "postponed": "⏸️"
        }.get(book.status, "📘")

        priority_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }.get(book.priority, "⚪")

        response += f"{i}. {status_emoji} {priority_emoji} **{book.title}** - {book.priority}\n"

    response += "\nПожалуйста, отправьте номер книги (например: '1'):"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=keyboards.cancel_keyboard())

    # Сохраняем состояние для следующих шагов
    context.user_data["state"] = "waiting_for_priority_change"
    context.user_data["user_id"] = user.id

async def handle_priority_book_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора книги для изменения приоритета."""
    try:
        user_id = context.user_data["user_id"]
        text = update.message.text.strip()

        # Парсим номер книги
        book_index = int(text) - 1  # Преобразуем в индекс (0-based)

        book_service = BookService()
        books = book_service.get_all_books(user_id)

        if book_index < 0 or book_index >= len(books):
            raise ValueError("Некорректный номер книги")

        book = books[book_index]

        # Показываем клавиатуру для выбора нового приоритета
        await update.message.reply_text(
            f"Вы выбрали книгу: **{book.title}**\n\n"
            "Пожалуйста, выберите новый приоритет:",
            reply_markup=keyboards.priority_keyboard(book.id),
            parse_mode="Markdown"
        )

        # Сохраняем ID книги для обновления
        context.user_data["priority_change_book_id"] = book.id
        context.user_data["state"] = "waiting_for_new_priority"

    except ValueError as e:
        await update.message.reply_text(
            f"❌ Некорректный ввод. Пожалуйста, отправьте номер книги (например: '1').\n"
            f"Ошибка: {str(e)}",
            reply_markup=keyboards.cancel_keyboard()
        )

async def handle_priority_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback для изменения приоритета книги."""
    query = update.callback_query

    data = query.data.split(":")
    if data[0] == "change_priority" and data[1] != "new_book":
        # Это изменение приоритета существующей книги
        try:
            book_id = data[1]
            new_priority = data[2]

            book_service = BookService()
            book = book_service.update_book_priority(book_id, new_priority)

            await query.edit_message_text(
                f"✅ Приоритет книги '{book.title}' изменён на '{book.priority}'"
            )
            await query.message.reply_text(
                "Что вы хотите сделать дальше?",
                reply_markup=keyboards.main_menu()
            )
        except Exception as e:
            log.error(f"Ошибка при изменении приоритета: {e}")
            await query.edit_message_text("❌ Произошла ошибка при изменении приоритета")
