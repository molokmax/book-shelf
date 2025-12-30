#!/usr/bin/env python3
"""Основной файл запуска Telegram-бота для Book Shelf."""

from utils import logger
from bot.bot import BookShelfBot

def main() -> None:
    """Запускает Telegram-бота."""
    # Настройка логирования
    log = logger.setup_logger(__name__)

    try:
        # Создание и запуск бота
        bot = BookShelfBot()
        bot.run()
    except Exception as e:
        log.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    main()
