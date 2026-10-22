"""Обработчик команды /progress: быстрое обновление прогресса чтения."""

from typing import Any

from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id

from core.models import ReadingStatus
from core.services import BookService
from utils import helpers
from vk_bot.flows.book_selection import BookSelectionFlow
from vk_bot.flows.progress_update import ProgressUpdateFlow
from vk_bot.user_helpers import get_or_create_user

from ..context import BotContext
from .base import AbstractCommandHandler


class ProgressHandler(AbstractCommandHandler):
    """Handler for the `/progress` command.

    Управляет состояниями:
    * selecting_reading_book: выбор книги из статуса «Читаю»
    * choose_filter, selecting_status_filter, selecting_tag_filter, selecting_book:
      стандартный диалог выбора книги через «Другие»
    * waiting_for_progress_input, waiting_for_progress_confirm:
      ввод и подтверждение прогресса
    """

    priority = 10
    commands = ["/progress", "progress", "прогресс"]

    def __init__(self) -> None:
        self._progress = ProgressUpdateFlow()
        self._selection = BookSelectionFlow(on_selected=self._on_book_selected)

    def handle(self, context: BotContext) -> Any:
        state_info = context.get_state()

        # Не перехватываем управление у активного сценария другой команды.
        if context.is_active() and state_info.get("command") != "/progress":
            return None

        if not context.is_active():
            self._handle_entry(context)
            return True

        state = state_info.get("state")
        if state == "selecting_reading_book":
            self._handle_selecting_reading_book(context)
        elif state in (
            "choose_filter",
            "selecting_status_filter",
            "selecting_tag_filter",
            "selecting_book",
        ):
            self._selection.handle(context)
        elif state in ("waiting_for_progress_input", "waiting_for_progress_confirm"):
            self._progress.handle(context)

        return True

    def _handle_entry(self, context: BotContext) -> None:
        user = get_or_create_user(context.api, context.user_id)
        state_info = {
            "command": "/progress",
            "state": "selecting_reading_book",
            "data": {"user_id": user.id},
        }
        context.set_state(state_info)
        self._show_reading_books(context)

    def _show_reading_books(self, context: BotContext) -> None:
        state_info = context.get_state()
        user_id = state_info["data"].get("user_id")
        if not user_id:
            user = get_or_create_user(context.api, context.user_id)
            user_id = user.id
            state_info["data"]["user_id"] = user_id

        books = BookService().filter_books(user_id, status=ReadingStatus.READING.value)
        if not books:
            self._selection.start(
                context,
                state_info,
                "Нет книг в статусе «Читаю». Выбери книгу:",
            )
            return

        books.sort(key=lambda book: book.updated_at, reverse=True)
        state_info["state"] = "selecting_reading_book"
        state_info["data"]["books"] = [book.id for book in books]
        context.set_state(state_info)

        lines = ["📚 Введи номер книги для обновления прогресса.\nКниги в статусе «Читаю»:\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        self._send(context, "".join(lines), self._create_reading_keyboard())

    def _handle_selecting_reading_book(self, context: BotContext) -> None:
        state_info = context.get_state()
        text = context.text.strip()

        if text.lower() == "другие":
            self._selection.start(context, state_info, "Какие книги интересуют?")
            return

        try:
            selection = int(text)
        except ValueError:
            self._send(
                context,
                helpers.format_invalid_input("Введи корректный номер книги."),
                self._create_reading_keyboard(),
            )
            return

        books_ids = state_info["data"].get("books", [])
        if selection < 1 or selection > len(books_ids):
            self._send(
                context,
                helpers.format_invalid_input("Номер книги вне диапазона."),
                self._create_reading_keyboard(),
            )
            return

        book = BookService().get_book_by_id(books_ids[selection - 1])
        if not book:
            self._send(context, "⚠️ Книга не найдена.", self._create_reading_keyboard())
            return

        self._on_book_selected(context, book)

    def _on_book_selected(self, context: BotContext, book) -> None:
        state_info = context.get_state()
        state_info["data"]["selected_book_id"] = book.id
        context.set_state(state_info)
        self._progress.start(context, state_info, book)

    @staticmethod
    def _create_reading_keyboard() -> VkKeyboard:
        """Клавиатура выбора книги из статуса «Читаю»."""
        kb = VkKeyboard()
        kb.add_button("Другие")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb

    @staticmethod
    def _send(context: BotContext, message: str, keyboard: VkKeyboard) -> None:
        context.api.messages.send(
            user_id=context.user_id,
            message=message,
            keyboard=keyboard.get_keyboard(),
            random_id=get_random_id(),
        )
