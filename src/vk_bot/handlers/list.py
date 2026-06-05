"""Handler for the /list command in the VK bot."""

from vk_api.utils import get_random_id

from core.services import BookService
from utils import helpers
from vk_bot.keyboards import (filter_keyboard, main_keyboard, status_keyboard,
                              tags_keyboard)
from vk_bot.user_helpers import get_or_create_user

# TODO: механизм вывода книг по категориям вынести отдельно, чтобы можно было использовать шаги из разных обработчиков


def handle_list_command(context) -> None:
    """Initiate the list command with filter options."""
    api = context.api
    user_id = context.user_id
    user = get_or_create_user(api, user_id)

    context.set_state(
        {
            "command": "/list",
            "state": "choose_filter",
            "data": {"user_id": user.id},
        }
    )

    api.messages.send(
        user_id=user_id,
        message="Какие книги интересуют?",
        keyboard=filter_keyboard().get_keyboard(),
        random_id=get_random_id(),
    )


def handle_list_command_step(context) -> None:
    """Process subsequent steps of the list command flow."""

    api = context.api
    user_id = context.user_id
    text = context.text
    payload = context.payload

    if not context.is_active():
        return

    user = get_or_create_user(api, user_id)

    state_info = context.get_state()
    state = state_info["state"]

    if state == "choose_filter":
        choice = text.strip().lower()
        if choice == "по статусу":
            # Show status keyboard
            api.messages.send(
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
            api.messages.send(
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
                    context,
                    "Твоя библиотека пуста. Добавь первую книгу с помощью /add",
                )
                return
            lines = ["📚 Твоя библиотека:\n\n"]
            for i, book in enumerate(books, 1):
                lines.append(helpers.format_book_info(i, book) + "\n")
            _finish(context, "".join(lines))
            return

        # Unrecognized input
        api.messages.send(
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
            _finish(context, "Книг с выбранным статусом нет.")
            return
        lines = [f"📚 Книги со статусом '{helpers.get_status_name(status)}':\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        _finish(context, "".join(lines))
        return

    if state == "choose_tag":
        # Filter by selected tag
        book_service = BookService()
        books = book_service.filter_books(user.id, tags=[text])
        books = helpers.sort_books_by_status(books)
        if not books:
            _finish(context, f"Книг с тегом '{text}' нет.")
            return
        lines = [f"📚 Книги с тегом '{text}':\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        _finish(context, "".join(lines))
        return


# Helper to finish and clean up state
def _finish(context, message: str, keyboard=None):
    api = context.api
    user_id = context.user_id
    api.messages.send(
        user_id=user_id,
        message=message,
        keyboard=(
            keyboard.get_keyboard() if keyboard else main_keyboard().get_keyboard()
        ),
        random_id=get_random_id(),
    )
    context.delete_state()
