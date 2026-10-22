"""Переиспользуемый диалог выбора книги по фильтрам.

TODO(#42): перевести EditHandler, DetailsHandler и ListHandler на этот компонент.
"""

from typing import Callable

from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id

from core.models import Book
from core.services import BookService
from utils import helpers
from vk_bot.context import BotContext
from vk_bot.keyboards import (
    cancel_keyboard,
    filter_keyboard,
    main_keyboard,
    status_keyboard,
    tags_keyboard,
)
from vk_bot.user_helpers import get_or_create_user


class BookSelectionFlow:
    """Диалог выбора книги: фильтр, список, номер книги.

    Компонент не знает, что делать с выбранной книгой. Решение принимает
    callback ``on_selected``.
    """

    def __init__(self, on_selected: Callable[[BotContext, Book], None]) -> None:
        self._on_selected = on_selected

    def start(
        self,
        context: BotContext,
        state_info: dict,
        message: str = "Какие книги интересуют?",
    ) -> None:
        """Открывает диалог на шаге выбора фильтра."""
        state_info["state"] = "choose_filter"
        state_info.setdefault("data", {}).setdefault("books", [])
        context.set_state(state_info)
        self._send(context, message, filter_keyboard())

    def handle(self, context: BotContext) -> None:
        """Обрабатывает текущее состояние диалога."""
        state_info = context.get_state()
        state = state_info.get("state")
        if state == "choose_filter":
            self._handle_choose_filter(context, state_info)
        elif state == "selecting_status_filter":
            self._handle_selecting_status_filter(context, state_info)
        elif state == "selecting_tag_filter":
            self._handle_selecting_tag_filter(context, state_info)
        elif state == "selecting_book":
            self._handle_selecting_book(context, state_info)

    def _handle_choose_filter(self, context: BotContext, state_info: dict) -> None:
        choice = context.text.strip().lower()
        if choice == "по статусу":
            state_info["state"] = "selecting_status_filter"
            context.set_state(state_info)
            self._send(context, "Выбери статус книги:", status_keyboard())
            return

        if choice == "по тегам":
            user_id = self._get_user_id(context, state_info)
            tags = BookService().get_all_tags(user_id)
            state_info["state"] = "selecting_tag_filter"
            context.set_state(state_info)
            self._send(context, "Выбери тег:", tags_keyboard(tags))
            return

        if choice == "все":
            user_id = self._get_user_id(context, state_info)
            books = helpers.sort_books_by_status(BookService().get_all_books(user_id))
            if not books:
                self._finish(context, "В библиотеке нет книг. Добавь книгу через /add")
                return
            self._show_books(
                context,
                state_info,
                books,
                "📚 Введи номер книги.\nТвоя библиотека:\n\n",
            )
            return

        self._send(
            context,
            helpers.format_invalid_input("Выбери: По статусу, По тегам, Все или Отмена."),
            filter_keyboard(),
        )

    def _handle_selecting_status_filter(self, context: BotContext, state_info: dict) -> None:
        payload = context.payload
        status = payload.get("status")
        if not status:
            self._send(
                context,
                helpers.format_invalid_input("Выбери статус из клавиатуры."),
                status_keyboard(),
            )
            return

        user_id = self._get_user_id(context, state_info)
        books = helpers.sort_books_by_status(BookService().filter_books(user_id, status=status))
        if not books:
            self._finish(context, "Книг с выбранным статусом нет.")
            return
        self._show_books(
            context,
            state_info,
            books,
            "📚 Введи номер книги.\nКниги с выбранным статусом:\n\n",
        )

    def _handle_selecting_tag_filter(self, context: BotContext, state_info: dict) -> None:
        selected_tag = context.text.strip()
        user_id = self._get_user_id(context, state_info)
        books = helpers.sort_books_by_status(
            BookService().filter_books(user_id, tags=[selected_tag])
        )
        if not books:
            self._finish(context, f"Книг с тегом '{selected_tag}' нет.")
            return
        self._show_books(
            context,
            state_info,
            books,
            "📚 Введи номер книги.\nКниги с выбранным тегом:\n\n",
        )

    def _handle_selecting_book(self, context: BotContext, state_info: dict) -> None:
        try:
            selection = int(context.text.strip())
        except ValueError:
            self._send(
                context,
                helpers.format_invalid_input("Введи корректный номер книги."),
                cancel_keyboard(),
            )
            return

        books_ids = state_info.get("data", {}).get("books", [])
        if selection < 1 or selection > len(books_ids):
            self._send(
                context,
                helpers.format_invalid_input("Номер книги вне диапазона."),
                cancel_keyboard(),
            )
            return

        book = BookService().get_book_by_id(books_ids[selection - 1])
        if not book:
            self._send(context, "⚠️ Книга не найдена.", cancel_keyboard())
            return

        self._on_selected(context, book)

    def _show_books(
        self,
        context: BotContext,
        state_info: dict,
        books: list[Book],
        header: str,
    ) -> None:
        state_info["state"] = "selecting_book"
        state_info["data"]["books"] = [book.id for book in books]
        context.set_state(state_info)

        lines = [header]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        self._send(context, "".join(lines), cancel_keyboard())

    def _get_user_id(self, context: BotContext, state_info: dict) -> str:
        user_id = state_info.get("data", {}).get("user_id")
        if not user_id:
            user = get_or_create_user(context.api, context.user_id)
            user_id = user.id
            state_info.setdefault("data", {})["user_id"] = user_id
            context.set_state(state_info)
        return user_id

    def _finish(self, context: BotContext, message: str) -> None:
        self._send(context, message, main_keyboard())
        context.delete_state()

    @staticmethod
    def _send(context: BotContext, message: str, keyboard: VkKeyboard) -> None:
        context.api.messages.send(
            user_id=context.user_id,
            message=message,
            keyboard=keyboard.get_keyboard(),
            random_id=get_random_id(),
        )
