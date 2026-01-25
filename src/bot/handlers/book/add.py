"""Обработчики команды /add и связанных с ней сообщений и callback-ов."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import logger, helpers
from core.services import BookService
from bot.keyboards import main as keyboards
from bot.keyboards.add_method import add_method_selection

log = logger.setup_logger(__name__)

async def add_book_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /add."""
    user = helpers.get_or_create_user(update)

    await update.message.reply_text(
        "📖 Добавление новой книги\n\n"
        "Пожалуйста, выберите способ добавления книги:",
        reply_markup=add_method_selection()
    )
    # Сохраняем состояние для выбора метода
    context.user_data["state"] = "selecting_add_method"
    context.user_data["user_id"] = user.id

async def handle_add_book_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик названия книги."""
    # Сохраняем название книги
    context.user_data["book_title"] = update.message.text.strip()
    await update.message.reply_text(
        "Отлично! Теперь введите автора книги:",
        reply_markup=keyboards.cancel_keyboard()
    )
    context.user_data["state"] = "waiting_for_author"

async def handle_add_book_author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик автора книги."""
    # Сохраняем автора
    context.user_data["book_author"] = update.message.text.strip()
    await update.message.reply_text(
        "Хорошо! Теперь введите теги книги через запятую (например: Tech, Программирование):",
        reply_markup=keyboards.cancel_keyboard()
    )
    context.user_data["state"] = "waiting_for_tags"

async def handle_add_book_tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик тегов книги."""
    # Сохраняем теги
    context.user_data["book_tags"] = [tag.strip() for tag in update.message.text.split(",") if tag.strip()]
    await update.message.reply_text(
        "Отлично! Теперь введите количество страниц в книге:",
        reply_markup=keyboards.cancel_keyboard()
    )
    context.user_data["state"] = "waiting_for_pages"

async def handle_add_book_pages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик количества страниц."""
    # Сохраняем количество страниц и запрашиваем приоритет
    pages = int(update.message.text.strip())
    if pages <= 0:
        raise ValueError

    user_id = context.user_data["user_id"]

    book_service = BookService()
    book = book_service.create_book(
        title=context.user_data["book_title"],
        author=context.user_data["book_author"],
        tags=context.user_data["book_tags"],
        pages=pages,
        user_id=user_id
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

async def handle_add_method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора метода добавления книги."""
    query = update.callback_query
    data = query.data.split(":")

    if len(data) < 2:
        return

    method = data[1]

    if method == "manual":
        # Ручное добавление книги
        await query.edit_message_text(
            "📖 Добавление новой книги\n\n"
            "Пожалуйста, введите название книги:",
            reply_markup=keyboards.cancel_keyboard()
        )
        # Сохраняем состояние для следующих шагов
        context.user_data["state"] = "waiting_for_title"
