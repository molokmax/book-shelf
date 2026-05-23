from vk_api.utils import get_random_id
from vk_api.vk_api import VkApiMethod

from vk_bot.keyboards import main_keyboard


def handle_start_command(vk: VkApiMethod, user_id: int):
    """Generate greeting text for the /start command."""
    greeting = (
        "Привет! Я твой персональный трекер чтения и менеджер книг.\n\n"
        "Что я могу сделать:\n"
        "/add - Добавить новую книгу\n"
        "/list - Показать список книг\n"
        "/edit - Редактировать книгу\n"
        "/stats - Статистика чтения\n"
        "/help - Помощь\n\n"
        "Начни с добавления первой книги!"
    )
    vk.messages.send(
        user_id=user_id,
        message=greeting,
        keyboard=main_keyboard().get_keyboard(),
        random_id=get_random_id(),
    )
