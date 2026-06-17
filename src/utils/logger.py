"""Настройка логирования для Book Shelf."""

import logging
import os
import sys
from typing import Optional


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """Настраивает и возвращает логгер."""
    logger = logging.getLogger(name)
    log_level = logging.DEBUG
    logger.setLevel(log_level)
    # Avoid adding duplicate handlers if already configured
    if logger.handlers:
        return logger

    # Устанавливаем формат
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Настраиваем обработчики
    console_handler = __create_console_handler(formatter, log_level)
    file_handler = __create_file_handler(formatter, log_level)

    # Добавляем обработчик
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def __create_console_handler(formatter: logging.Formatter, level):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    return handler


def __create_file_handler(formatter: logging.Formatter, level):
    log_dir = "logs"
    log_file = "app.log"
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception:
        pass
    handler = logging.FileHandler(os.path.join(log_dir, log_file), encoding="utf-8")
    handler.setFormatter(formatter)
    handler.setLevel(level)
    return handler
