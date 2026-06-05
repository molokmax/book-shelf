from vk_api.utils import get_random_id

from vk_bot.keyboards import main_keyboard


def handle_help_command(context):
    """Send help information for the bot."""
    help_text = (
        "📚 Book Shelf - Персональный трекер чтения\n\n"
        "💬 Доступные команды\n"
        "* /start - Начало работы\n"
        "* /add - Добавить новую книгу\n"
        "* /list - Показать список книг\n"
        "* /edit - Редактировать книгу\n"
        "* /export - Экспорт списка книг в CSV\n"
        "* /stats - Статистика чтения\n"
        "* /cancel - Отмена текущей операции\n\n"
        "📖 Добавление книги\n"
        "Используйте команду /add и следуйте инструкциям.\n"
        "Вы можете указать: название, автора, теги, количество страниц.\n\n"
        "📊 Управление статусами\n"
        "После добавления книги вы можете изменить её статус:\n"
        "* Хочу прочитать\n"
        "* Читаю сейчас\n"
        "* Прочитано\n"
        "* Отложено\n\n"
        "🎯 Приоритеты\n"
        "Установите приоритет: Высокий, Средний, Низкий"
    )
    context.api.messages.send(
        user_id=context.user_id,
        message=help_text,
        keyboard=main_keyboard().get_keyboard(),
        random_id=get_random_id(),
    )
