#!/usr/bin/env python3
"""Основной файл запуска Telegram-бота для Book Shelf."""

import logging
from bot.bot import BookShelfBot

def main() -> None:
    """Запускает Telegram-бота."""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    try:
        # Создание и запуск бота
        bot = BookShelfBot()
        bot.run()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    main()
