"""Настройка логирования для Book Shelf."""

import logging
from typing import Optional

def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """Настраивает и возвращает логгер."""
    logger = logging.getLogger(name)

    # Устанавливаем формат
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Настраиваем обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Добавляем обработчик
    logger.addHandler(console_handler)

    # Устанавливаем уровень логирования
    logger.setLevel(logging.INFO)

    return logger
