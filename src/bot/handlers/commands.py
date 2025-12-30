"""Обработчики команд для Telegram-бота."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import logger
from core.services import BookService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! 📚\n\n"
        "Я - ваш персональный трекер чтения и менеджер книг. 📚\n\n"
        "Что я могу сделать:\n"
        "/add - Добавить новую книгу\n"
        "/list - Показать список книг\n"
        "/stats - Статистика чтения\n"
        "/help - Помощь\n\n"
        "Начните с добавления первой книги!",
        reply_markup=keyboards.main_menu()
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    help_text = (
        "📚 **Book Shelf - Персональный трекер чтения**\n\n"
        "Доступные команды:\n\n"
        "• `/start` - Начало работы\n"
        "• `/add` - Добавить новую книгу\n"
        "• `/list` - Показать список книг\n"
        "• `/stats` - Статистика чтения\n"
        "• `/export` - Экспортировать библиотеку\n\n"
        "📖 **Добавление книги:**\n"
        "Используйте команду `/add` и следуйте инструкциям.\n"
        "Вы можете указать: название, автора, теги, количество страниц.\n\n"
        "📊 **Управление статусами:**\n"
        "После добавления книги вы можете изменить её статус:\n"
        "• Хочу прочитать\n"
        "• Читаю сейчас\n"
        "• Прочитано\n"
        "• Отложено\n\n"
        "🎯 **Приоритеты:**\n"
        "Установите приоритет: Высокий, Средний, Низкий"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def add_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /add."""
    await update.message.reply_text(
        "📖 Добавление новой книги\n\n"
        "Пожалуйста, введите название книги:",
        reply_markup=keyboards.cancel_keyboard()
    )
    # Сохраняем состояние для следующих шагов
    context.user_data["state"] = "waiting_for_title"

async def list_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /list."""
    book_service = BookService()
    books = book_service.get_all_books()

    if not books:
        await update.message.reply_text("Ваша библиотека пуста. Добавьте первую книгу с помощью /add")
        return

    response = "📚 Ваша библиотека:\n\n"
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

        tags_text = ", ".join(book.tags) if book.tags else "Нет тегов"
        response += (
            f"{i}. {status_emoji} {priority_emoji} **{book.title}**\n"
            f"   *Автор:* {book.author}\n"
            f"   *Теги:* {tags_text}\n"
            f"   *Страниц:* {book.pages}\n"
            f"   *Прогресс:* {book.progress}%\n\n"
        )

    await update.message.reply_text(response, parse_mode="Markdown")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /stats."""
    book_service = BookService()
    stats_data = book_service.get_stats()

    stats_text = (
        "📊 **Статистика чтения**\n\n"
        f"• Всего книг: {stats_data['total_books']}\n"
        f"• Прочитано: {stats_data['read_books']}\n"
        f"• Читаю сейчас: {stats_data['reading_books']}\n"
        f"• Хочу прочитать: {stats_data['want_to_read_books']}\n"
        f"• Отложено: {stats_data['postponed_books']}\n\n"
        f"• Всего страниц: {stats_data['total_pages']}\n"
        f"• Прочитано страниц: {stats_data['read_pages']}\n"
        f"• Средний прогресс: {stats_data['avg_progress']:.1f}%\n"
    )

    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /export."""
    book_service = BookService()
    export_data = book_service.export_library()

    await update.message.reply_text(
        "📥 Экспорт библиотеки завершён!\n\n"
        "Данные сохранены в файл. Вы можете загрузить его или использовать для резервного копирования.",
        reply_markup=keyboards.main_menu()
    )
