from vk_api.vk_api import VkApiMethod
from vk_api.keyboard import VkKeyboard

def handle_start_command(vk: VkApiMethod, user_id):
    """Generate greeting text for the /start command."""
    greeting = (
        "Привет! Я ваш персональный трекер чтения и менеджер книг.\n\n"
        "Что я могу сделать:\n"
        "/add - Добавить новую книгу\n"
        "/list - Показать список книг\n"
        "/edit - Редактировать книгу\n"
        "/stats - Статистика чтения\n"
        "/help - Помощь\n\n"
        "Начни с добавления первой книги!"
    )
    keyboard = create_start_keyboard()
    vk.messages.send(user_id=user_id, message=greeting, keyboard=keyboard.get_keyboard(), random_id=0)
    
    
def create_start_keyboard() -> VkKeyboard:
    """Create the keyboard for the /start command."""
    kb = VkKeyboard()
    kb.add_button('/add')
    kb.add_button('/list')
    kb.add_button('/edit')
    kb.add_button('/stats')
    kb.add_button('/help')
    return kb