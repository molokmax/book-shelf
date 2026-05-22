"""Handler for the /list command in the VK bot."""

from vk_api.utils import get_random_id
from vk_api.vk_api import VkApiMethod

from core.services import BookService
from utils import helpers
from vk_bot.keyboards import main_keyboard
from vk_bot.user_helpers import get_or_create_user


def handle_list_command(vk: VkApiMethod, user_id: int) -> None:
    """Send the list of books for the given VK ``user_id``."""
    # 1. Ensure we have a user entry in the system.
    user = get_or_create_user(vk, user_id)

    # 2. Retrieve books for this user.
    book_service = BookService()
    books = book_service.get_all_books(user.id)
    books = helpers.sort_books_by_status(books)

    # 3. Build response text.
    if not books:
        message = "Твоя библиотека пуста. Добавь первую книгу с помощью /add"
    else:
        lines = ["📚 Твоя библиотека:\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        message = "".join(lines)

    # 4. Send the message via VK API.
    vk.messages.send(
        user_id=user_id,
        message=message,
        keyboard=main_keyboard().get_keyboard(),
        random_id=get_random_id()
    )
