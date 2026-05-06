from vk_api.vk_api import VkApiMethod
from keyboards import start_keyboard

def handle_help_command(vk: VkApiMethod, user_id):
    """Send help information for the bot."""
    help_text = (
        "📚 Book Shelf - Персональный трекер чтения\n\n"
        "Доступные команды:\n\n"
        "* /start - Начало работы\n"
        "* /add - Добавить новую книгу\n"
        "* /list - Показать список книг\n"
        "* /edit - Редактировать книгу\n"
        "* /stats - Статистика чтения\n"
        "* /cancel - Отмена текущей операции\n\n"
        "📖 Добавление книги:\n"
        "Используйте команду /add и следуйте инструкциям.\n"
        "Вы можете указать: название, автора, теги, количество страниц.\n\n"
        "📊 Управление статусами:\n"
        "После добавления книги вы можете изменить её статус:\n"
        "* Хочу прочитать\n"
        "* Читаю сейчас\n"
        "* Прочитано\n"
        "* Отложено\n\n"
        "🎯 Приоритеты:\n"
        "Установите приоритет: Высокий, Средний, Низкий"
    )
    keyboard = start_keyboard()
    vk.messages.send(user_id=user_id, message=help_text, keyboard=keyboard.get_keyboard(), random_id=0)
