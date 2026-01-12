"""Основной класс Telegram-бота для Book Shelf."""

import logging
from typing import Optional
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from utils.config import load_config
from bot.handlers import commands, messages, callbacks
from bot.keyboards import main as keyboards

class BookShelfBot:
    """Основной класс Telegram-бота."""

    def __init__(self) -> None:
        """Инициализация бота."""
        load_dotenv()
        self.logger = logging.getLogger(__name__)
        self.config = load_config()
        self.application: Optional[Application] = None

    def setup_handlers(self) -> None:
        """Настройка обработчиков."""
        if not self.application:
            return

        # Обработчики команд
        self.application.add_handler(CommandHandler("start", commands.start))
        self.application.add_handler(CommandHandler("help", commands.help))
        self.application.add_handler(CommandHandler("add", commands.add_book))
        self.application.add_handler(CommandHandler("list", commands.list_books))
        self.application.add_handler(CommandHandler("stats", commands.stats))
        self.application.add_handler(CommandHandler("export", commands.export))
        self.application.add_handler(CommandHandler("progress", commands.update_progress))
        self.application.add_handler(CommandHandler("priority", commands.change_priority))

        # Обработчики сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages.handle_text))

        # Обработчики callback-queries
        self.application.add_handler(CallbackQueryHandler(callbacks.handle_callback))

    def run(self) -> None:
        """Запуск бота."""
        self.logger.info("Инициализация бота...")

        try:
            self.application = Application.builder().token(self.config.bot_token).build()

            # Настройка обработчиков
            self.setup_handlers()

            # Запуск бота
            self.logger.info("Бот запущен и ожидает сообщений...")
            self.application.run_polling()

        except Exception as e:
            self.logger.error(f"Ошибка при запуске бота: {e}")
            raise
