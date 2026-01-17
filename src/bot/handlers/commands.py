"""Обработчики команд для Telegram-бота."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import logger
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
        "/edit - Редактировать книгу\n"
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
        "• `/edit` - Редактировать книгу\n"
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
