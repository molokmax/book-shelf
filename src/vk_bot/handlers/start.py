from vk_api.utils import get_random_id

from vk_bot.keyboards import main_keyboard


def handle_start_command(context):
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
    context.api.messages.send(
        user_id=context.user_id,
        message=greeting,
        keyboard=main_keyboard().get_keyboard(),
        random_id=get_random_id(),
    )
