"""Переиспользуемый диалог выбора книги по фильтрам.

TODO(#42): перевести EditHandler, DetailsHandler и ListHandler на этот компонент.
"""

from typing import Callable

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
from vk_bot.navigation import available_back_command, record_transition
from vk_bot.states import SelectionState
from vk_bot.user_helpers import get_or_create_user


class BookSelectionFlow:
    """Диалог выбора книги: фильтр, список, номер книги.

    Компонент не знает, что делать с выбранной книгой. Решение принимает
    callback ``on_selected``.
    """

    def __init__(
        self,
        owner_command: str,
        on_selected: Callable[[BotContext, Book], None],
    ) -> None:
        self._owner_command = owner_command
        self._on_selected = on_selected

    def start(
        self,
        context: BotContext,
        state_info: dict,
        message: str = "Какие книги интересуют?",
    ) -> None:
        """Открывает диалог на шаге выбора фильтра."""
        record_transition(state_info, SelectionState.CHOOSE_FILTER)
        state_info.setdefault("data", {}).setdefault("books", [])
        context.set_state(state_info)
        context.send_message(message, keyboard=self._filter_keyboard(state_info))

    def render_current(self, context: BotContext, state_info: dict) -> None:
        """Перерисовывает текущий шаг диалога после возврата «Назад»."""
        state = state_info.get("state")
        if state == SelectionState.CHOOSE_FILTER:
            context.send_message(
                "Какие книги интересуют?", keyboard=self._filter_keyboard(state_info)
            )
        elif state == SelectionState.SELECTING_STATUS_FILTER:
            context.send_message(
                "Выбери статус книги:",
                keyboard=status_keyboard(self._back_command(state_info)),
            )
        elif state == SelectionState.SELECTING_TAG_FILTER:
            tags = BookService().get_all_tags(self._get_user_id(context, state_info))
            context.send_message(
                "Выбери тег:",
                keyboard=tags_keyboard(tags, self._back_command(state_info)),
            )
        elif state == SelectionState.SELECTING_BOOK:
            data = state_info["data"]
            context.send_message(
                data["list_header"] + "".join(data["book_lines"]),
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )

    def _back_command(self, state_info: dict) -> str | None:
        return available_back_command(state_info, self._owner_command)

    def _filter_keyboard(self, state_info: dict):
        return filter_keyboard(self._back_command(state_info))

    def handle(self, context: BotContext) -> None:
        """Обрабатывает текущее состояние диалога."""
        state_info = context.get_state()
        state = state_info.get("state")
        if state == SelectionState.CHOOSE_FILTER:
            self._handle_choose_filter(context, state_info)
        elif state == SelectionState.SELECTING_STATUS_FILTER:
            self._handle_selecting_status_filter(context, state_info)
        elif state == SelectionState.SELECTING_TAG_FILTER:
            self._handle_selecting_tag_filter(context, state_info)
        elif state == SelectionState.SELECTING_BOOK:
            self._handle_selecting_book(context, state_info)

    def _handle_choose_filter(self, context: BotContext, state_info: dict) -> None:
        choice = context.text.strip().lower()
        if choice == "по статусу":
            record_transition(state_info, SelectionState.SELECTING_STATUS_FILTER)
            context.set_state(state_info)
            context.send_message(
                "Выбери статус книги:",
                keyboard=status_keyboard(self._back_command(state_info)),
            )
            return

        if choice == "по тегам":
            user_id = self._get_user_id(context, state_info)
            tags = BookService().get_all_tags(user_id)
            record_transition(state_info, SelectionState.SELECTING_TAG_FILTER)
            context.set_state(state_info)
            context.send_message(
                "Выбери тег:",
                keyboard=tags_keyboard(tags, self._back_command(state_info)),
            )
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

        context.send_message(
            helpers.format_invalid_input("Выбери: По статусу, По тегам, Все или Отмена."),
            keyboard=self._filter_keyboard(state_info),
        )

    def _handle_selecting_status_filter(self, context: BotContext, state_info: dict) -> None:
        payload = context.payload
        status = payload.get("status")
        if not status:
            context.send_message(
                helpers.format_invalid_input("Выбери статус из клавиатуры."),
                keyboard=status_keyboard(self._back_command(state_info)),
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
            context.send_message(
                helpers.format_invalid_input("Введи корректный номер книги."),
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )
            return

        books_ids = state_info.get("data", {}).get("books", [])
        if selection < 1 or selection > len(books_ids):
            context.send_message(
                helpers.format_invalid_input("Номер книги вне диапазона."),
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )
            return

        book = BookService().get_book_by_id(books_ids[selection - 1])
        if not book:
            context.send_message(
                "⚠️ Книга не найдена.", keyboard=cancel_keyboard(self._back_command(state_info))
            )
            return

        self._on_selected(context, book)

    def _show_books(
        self,
        context: BotContext,
        state_info: dict,
        books: list[Book],
        header: str,
    ) -> None:
        record_transition(state_info, SelectionState.SELECTING_BOOK)
        state_info["data"]["books"] = [book.id for book in books]
        # Заголовок и строки списка сохраняем, чтобы перерисовать экран
        # после возврата «Назад» без повторного запроса к сервису
        state_info["data"]["list_header"] = header
        state_info["data"]["book_lines"] = [
            helpers.format_book_info(i, book) + "\n" for i, book in enumerate(books, 1)
        ]
        context.set_state(state_info)

        lines = [header]
        lines.extend(state_info["data"]["book_lines"])
        context.send_message(
            "".join(lines), keyboard=cancel_keyboard(self._back_command(state_info))
        )

    def _get_user_id(self, context: BotContext, state_info: dict) -> str:
        user_id = state_info.get("data", {}).get("user_id")
        if not user_id:
            user = get_or_create_user(context.api, context.user_id)
            user_id = user.id
            state_info.setdefault("data", {})["user_id"] = user_id
            context.set_state(state_info)
        return user_id

    def _finish(self, context: BotContext, message: str) -> None:
        # Финал: отправляем до delete_state, чтобы удалить висящий промпт.
        context.send_message(message, keyboard=main_keyboard())
        context.delete_state()
