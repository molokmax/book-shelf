from vk_api.vk_api import VkApiMethod
from keyboards import start_keyboard

def handle_start_command(vk: VkApiMethod, user_id):
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
    keyboard = start_keyboard()
    vk.messages.send(user_id=user_id, message=greeting, keyboard=keyboard.get_keyboard(), random_id=0)
