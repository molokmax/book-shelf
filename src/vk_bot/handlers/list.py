"""Handler for the /list command in the VK bot."""

from vk_api.utils import get_random_id
from vk_api.vk_api import VkApiMethod

from core.services import BookService
from utils import helpers
from vk_bot.keyboards import (
    filter_keyboard,
    main_keyboard,
    status_keyboard,
    tags_keyboard,
)
from vk_bot.states import active_states
from vk_bot.user_helpers import get_or_create_user

# TODO: механизм вывода книг по категориям вынести отдельно, чтобы можно было использовать шаги из разных обработчиков


def handle_list_command(vk: VkApiMethod, user_id: int) -> None:
    """Initiate the list command with filter options."""
    # Ensure we have a user entry in the system.
    user = get_or_create_user(vk, user_id)

    active_states[user_id] = {
        "command": "/list",
        "state": "choose_filter",
        "data": {"user_id": user.id},
    }

    # Show filter keyboard.
    vk.messages.send(
        user_id=user_id,
        message="Какие книги интересуют?",
        keyboard=filter_keyboard().get_keyboard(),
        random_id=get_random_id(),
    )


def handle_list_command_step(
    vk: VkApiMethod, user_id: int, text: str, payload: dict[str, str]
) -> None:
    """Process subsequent steps of the list command flow."""

    if user_id not in active_states:
        return

    user = get_or_create_user(vk, user_id)

    state_info = active_states[user_id]
    state = state_info["state"]

    if state == "choose_filter":
        choice = text.strip().lower()
        if choice == "по статусу":
            # Show status keyboard
            vk.messages.send(
                user_id=user_id,
                message="Выбери статус книги:",
                keyboard=status_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            state_info["state"] = "choose_status"
            return

        if choice == "по тегам":
            # Need list of tags
            book_service = BookService()
            tags = book_service.get_all_tags(user.id)
            vk.messages.send(
                user_id=user_id,
                message="Выбери тег:",
                keyboard=tags_keyboard(tags).get_keyboard(),
                random_id=get_random_id(),
            )
            state_info["state"] = "choose_tag"
            return

        if choice == "все":
            # Show all books
            book_service = BookService()
            books = book_service.get_all_books(user.id)
            books = helpers.sort_books_by_status(books)
            if not books:
                _finish(
                    vk,
                    user_id,
                    "Твоя библиотека пуста. Добавь первую книгу с помощью /add",
                )
                return
            lines = ["📚 Твоя библиотека:\n\n"]
            for i, book in enumerate(books, 1):
                lines.append(helpers.format_book_info(i, book) + "\n")
            _finish(vk, user_id, "".join(lines))
            return

        # Unrecognized input
        vk.messages.send(
            user_id=user_id,
            message="Пожалуйста, выбери один из вариантов: По статусу, По тегам, Все, Отмена.",
            keyboard=filter_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    if state == "choose_status":
        # Assume status value matches ReadingStatus values
        book_service = BookService()
        status = payload.get("status", "")
        books = book_service.filter_books(user.id, status=status)
        books = helpers.sort_books_by_status(books)
        if not books:
            _finish(vk, user_id, "Книг с выбранным статусом нет.")
            return
        lines = [f"📚 Книги со статусом '{helpers.get_status_name(status)}':\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        _finish(vk, user_id, "".join(lines))
        return

    if state == "choose_tag":
        # Filter by selected tag
        book_service = BookService()
        books = book_service.filter_books(user.id, tags=[text])
        books = helpers.sort_books_by_status(books)
        if not books:
            _finish(vk, user_id, f"Книг с тегом '{text}' нет.")
            return
        lines = [f"📚 Книги с тегом '{text}':\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        _finish(vk, user_id, "".join(lines))
        return


# Helper to finish and clean up state
def _finish(vk: VkApiMethod, user_id: int, message: str, keyboard=None):
    vk.messages.send(
        user_id=user_id,
        message=message,
        keyboard=(
            keyboard.get_keyboard() if keyboard else main_keyboard().get_keyboard()
        ),
        random_id=get_random_id(),
    )
    del active_states[user_id]
