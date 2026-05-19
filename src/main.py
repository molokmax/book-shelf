#!/usr/bin/env python3
"""Entry point for VK bot.

Runs the VkBookShelfBot defined in ``src/vk_bot/bot.py``. The bot reads
``BOT_TOKEN`` from the environment (see ``bot.py``) and starts the event
loop. Adjust any routing inside ``VkBookShelfBot.run`` as needed.
"""

from utils import logger
from vk_bot.bot import VkBookShelfBot


def main() -> None:
    """Run the VK bot."""
    log = logger.setup_logger(__name__)
    try:
        bot = VkBookShelfBot()
        bot.run()
    except Exception as e:
        log.error(f"Ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    main()
