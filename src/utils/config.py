"""Конфигурация приложения."""

import os
from dataclasses import dataclass

@dataclass
class Config:
    """Конфигурация бота."""
    bot_token: str
    data_dir: str = "data"
    debug: bool = False

def load_config() -> Config:
    """Загружает конфигурацию из переменных окружения."""
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN не установлен в переменных окружения")

    return Config(
        bot_token=bot_token,
        data_dir=os.getenv("DATA_DIR", "data"),
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )
