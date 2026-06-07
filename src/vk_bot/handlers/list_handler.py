"""List command handler as AbstractCommandHandler subclass."""

from typing import Any

from vk_api.utils import get_random_id

from core.services import BookService
from utils import helpers
from vk_bot.keyboards import (
    filter_keyboard,
    main_keyboard,
    status_keyboard,
    tags_keyboard,
)
from vk_bot.user_helpers import get_or_create_user

from ..context import BotContext
from .base import AbstractCommandHandler


class ListHandler(AbstractCommandHandler):
    priority = 10
    commands = ["/list", "list"]

    def handle(self, context: BotContext) -> Any:
        if context.is_active():
            state = context.get_state()["state"]
            method = getattr(self, f"_handle_{state}")
            method(context)
        else:
            self._handle_entry(context)
        return True

    def _handle_entry(self, context: BotContext) -> None:
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

    def _handle_choose_filter(self, context: BotContext) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        user = get_or_create_user(api, user_id)

        choice = text.strip().lower()
        if choice == "по статусу":
            api.messages.send(
                user_id=user_id,
                message="Выбери статус книги:",
                keyboard=status_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            state_info = context.get_state()
            state_info["state"] = "choose_status"
            return

        if choice == "по тегам":
            book_service = BookService()
            tags = book_service.get_all_tags(user.id)
            api.messages.send(
                user_id=user_id,
                message="Выбери тег:",
                keyboard=tags_keyboard(tags).get_keyboard(),
                random_id=get_random_id(),
            )
            state_info = context.get_state()
            state_info["state"] = "choose_tag"
            return

        if choice == "все":
            book_service = BookService()
            books = book_service.get_all_books(user.id)
            books = helpers.sort_books_by_status(books)
            if not books:
                self._finish(context, "Твоя библиотека пуста. Добавь книгу через /add")
                return
            lines = ["📚 Твоя библиотека:\n\n"]
            for i, book in enumerate(books, 1):
                lines.append(helpers.format_book_info(i, book) + "\n")
            self._finish(context, "".join(lines))
            return

        api.messages.send(
            user_id=user_id,
            message="Выбери: По статусу, По тегам, Все или Отмена.",
            keyboard=filter_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_choose_status(self, context: BotContext) -> None:
        api = context.api
        user_id = context.user_id
        payload = context.payload
        user = get_or_create_user(api, user_id)

        book_service = BookService()
        status = payload.get("status", "")
        books = book_service.filter_books(user.id, status=status)
        books = helpers.sort_books_by_status(books)
        if not books:
            self._finish(context, "Книг с выбранным статусом нет.")
            return
        lines = [f"📚 Книги со статусом '{helpers.get_status_name(status)}':\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        self._finish(context, "".join(lines))

    def _handle_choose_tag(self, context: BotContext) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        user = get_or_create_user(api, user_id)

        book_service = BookService()
        books = book_service.filter_books(user.id, tags=[text])
        books = helpers.sort_books_by_status(books)
        if not books:
            self._finish(context, f"Книг с тегом '{text}' нет.")
            return
        lines = [f"📚 Книги с тегом '{text}':\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        self._finish(context, "".join(lines))

    def _finish(self, context: BotContext, message: str, keyboard=None):
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
