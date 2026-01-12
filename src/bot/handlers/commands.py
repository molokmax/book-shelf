"""Обработчики команд для Telegram-бота."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import logger
from core.services import BookService, UserService
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
        "/progress - Обновить прогресс чтения\n"
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
        "• `/progress` - Обновить прогресс чтения\n"
        "• `/stats` - Статистика чтения\n"
        "• `/export` - Экспортировать библиотеку\n\n"
        "📖 **Добавление книги:**\n"
        "Используйте команду `/add` и следуйте инструкциям.\n"
        "Вы можете указать: название, автора, теги, количество страниц.\n\n"
        "📊 **Обновление прогресса:**\n"
        "Используйте команду `/progress` и следуйте инструкциям.\n"
        "Укажите номер книги и текущую страницу (например: '1 50').\n\n"
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
    # Получаем или создаём пользователя
    user_service = UserService()
    user = user_service.get_or_create_user(
        update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name
    )

    await update.message.reply_text(
        "📖 Добавление новой книги\n\n"
        "Пожалуйста, введите название книги:",
        reply_markup=keyboards.cancel_keyboard()
    )
    # Сохраняем состояние для следующих шагов
    context.user_data["state"] = "waiting_for_title"
    context.user_data["user_id"] = user.id

async def list_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /list."""
    # Получаем или создаём пользователя
    user_service = UserService()
    user = user_service.get_or_create_user(
        update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name
    )

    book_service = BookService()
    books = book_service.get_all_books(user.id)

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
    # Получаем или создаём пользователя
    user_service = UserService()
    user = user_service.get_or_create_user(
        update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name
    )

    book_service = BookService()
    stats_data = book_service.get_stats(user.id)

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
    # Получаем или создаём пользователя
    user_service = UserService()
    user = user_service.get_or_create_user(
        update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name
    )

    book_service = BookService()
    export_data = book_service.export_library(user.id)

    await update.message.reply_text(
        "📥 Экспорт библиотеки завершён!\n\n"
        "Данные сохранены в файл. Вы можете загрузить его или использовать для резервного копирования.",
        reply_markup=keyboards.main_menu()
    )

async def update_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /progress."""
    # Получаем или создаём пользователя
    user_service = UserService()
    user = user_service.get_or_create_user(
        update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name
    )

    book_service = BookService()
    books = book_service.get_all_books(user.id)

    if not books:
        await update.message.reply_text("Ваша библиотека пуста. Добавьте первую книгу с помощью /add")
        return

    # Показываем список книг с их текущим прогрессом
    response = "📚 Выберите книгу для обновления прогресса:\n\n"
    for i, book in enumerate(books, 1):
        status_emoji = {
            "want_to_read": "📖",
            "reading": "📚",
            "read": "📕",
            "postponed": "⏸️"
        }.get(book.status, "📘")

        response += f"{i}. {status_emoji} **{book.title}** - Страница {book.progress}/{book.pages}\n"

    response += "\nПожалуйста, отправьте номер книги и текущую страницу (например: '1 50' для страницы 50):"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=keyboards.cancel_keyboard())

    # Сохраняем состояние для следующих шагов
    context.user_data["state"] = "waiting_for_progress_update"
    context.user_data["user_id"] = user.id

async def change_priority(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /priority."""
    # Получаем или создаём пользователя
    user_service = UserService()
    user = user_service.get_or_create_user(
        update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name
    )

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
