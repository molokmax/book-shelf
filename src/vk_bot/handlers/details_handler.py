"""Обработчик команды /details.

Содержит всю логику многошагового процесса:
выбор фильтра → выбор книги → показ деталей.
"""

from datetime import datetime, timedelta
from typing import Any

from vk_api.utils import get_random_id

from core.services import BookService, ReadingStatsService
from utils import helpers, logger
from utils.helpers import format_book_details
from vk_bot.keyboards import (
    cancel_keyboard,
    filter_keyboard,
    main_keyboard,
    status_keyboard,
    tags_keyboard,
)
from vk_bot.user_helpers import get_or_create_user

from ..context import BotContext
from .base import AbstractCommandHandler

log = logger.setup_logger(__name__)


class DetailsHandler(AbstractCommandHandler):
    """Handler for the `/details` command.

    Управляет состояниями:
    * choose_filter → выбор фильтра (по статусу / по тегам / все)
    * selecting_status_filter → выбор статуса
    * selecting_tag_filter → выбор тега
    * selecting_book → выбор книги и показ деталей
    """

    priority = 10
    commands = ["/details", "details"]

    def handle(self, context: BotContext) -> Any:
        if not context.is_active():
            self._handle_entry(context)
            return True

        state_info = context.get_state()
        if not state_info or state_info.get("command") != "/details":
            return True

        state = state_info.get("state")
        if state == "choose_filter":
            self._handle_choose_filter(context)
        elif state == "selecting_status_filter":
            self._handle_selecting_status_filter(context)
        elif state == "selecting_tag_filter":
            self._handle_selecting_tag_filter(context)
        elif state == "selecting_book":
            self._handle_selecting_book(context)

        return True

    def _handle_entry(self, context) -> None:
        api = context.api
        user_id = context.user_id
        user = get_or_create_user(api, user_id)
        context.set_state(
            {
                "command": "/details",
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

    def _handle_choose_filter(self, context) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        state_info = context.get_state()
        user = get_or_create_user(api, user_id)

        choice = text.strip().lower()
        if choice == "по статусу":
            state_info["state"] = "selecting_status_filter"
            api.messages.send(
                user_id=user_id,
                message="Выбери статус книги:",
                keyboard=status_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        if choice == "по тегам":
            book_service = BookService()
            tags = book_service.get_all_tags(user.id)
            state_info["state"] = "selecting_tag_filter"
            api.messages.send(
                user_id=user_id,
                message="Выбери тег:",
                keyboard=tags_keyboard(tags).get_keyboard(),
                random_id=get_random_id(),
            )
            return

        if choice == "все":
            book_service = BookService()
            books = book_service.get_all_books(user.id)
            books = helpers.sort_books_by_status(books)
            if not books:
                api.messages.send(
                    user_id=user_id,
                    message="В библиотеке нет книг. Добавь книгу через /add",
                    keyboard=main_keyboard().get_keyboard(),
                    random_id=get_random_id(),
                )
                context.delete_state()
                return
            state_info["state"] = "selecting_book"
            state_info["data"]["books"] = [book.id for book in books]
            lines = ["📚 Введи номер книги.\nТвоя библиотека:\n\n"]
            for i, book in enumerate(books, 1):
                lines.append(helpers.format_book_info(i, book) + "\n")
            api.messages.send(
                user_id=user_id,
                message="".join(lines),
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        api.messages.send(
            user_id=user_id,
            message="⚠️ Выбери: По статусу, По тегам или Все",
            keyboard=filter_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_selecting_status_filter(self, context) -> None:
        api = context.api
        user_id = context.user_id
        payload = context.payload
        state_info = context.get_state()
        user = get_or_create_user(api, user_id)

        status = payload.get("status", "")
        book_service = BookService()
        books = book_service.filter_books(user.id, status=status)
        books = helpers.sort_books_by_status(books)
        if not books:
            api.messages.send(
                user_id=user_id,
                message="Книг с выбранным статусом нет.",
                keyboard=main_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            context.delete_state()
            return

        state_info["state"] = "selecting_book"
        state_info["data"]["books"] = [book.id for book in books]
        lines = ["📚 Введи номер книги.\nКниги с выбранным статусом:\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        api.messages.send(
            user_id=user_id,
            message="".join(lines),
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_selecting_tag_filter(self, context) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        state_info = context.get_state()
        user = get_or_create_user(api, user_id)

        selected_tag = text.strip()
        book_service = BookService()
        books = book_service.filter_books(user.id, tags=[selected_tag])
        books = helpers.sort_books_by_status(books)
        if not books:
            api.messages.send(
                user_id=user_id,
                message="Книг с выбранным тегом нет.",
                keyboard=main_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            context.delete_state()
            return

        state_info["state"] = "selecting_book"
        state_info["data"]["books"] = [book.id for book in books]
        lines = ["📚 Введи номер книги.\nКниги с выбранным тегом:\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        api.messages.send(
            user_id=user_id,
            message="".join(lines),
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_selecting_book(self, context) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        state_info = context.get_state()

        try:
            selection = int(text.strip())
        except ValueError:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Введи корректный номер книги.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        books_ids = state_info["data"]["books"]
        if selection < 1 or selection > len(books_ids):
            api.messages.send(
                user_id=user_id,
                message="⚠️ Номер книги вне диапазона.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        book_id = books_ids[selection - 1]
        book = BookService().get_book_by_id(book_id)
        if not book:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        stats_service = ReadingStatsService()
        today = datetime.now().replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        week_start = (today - timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        month_start = (today - timedelta(days=30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        weekly_pages = stats_service.get_reading_stats(book.id, week_start, today)
        monthly_pages = stats_service.get_reading_stats(book.id, month_start, today)
        avg_pages = stats_service.avg_pages_per_day(book)
        pred_date = stats_service.predict_completion_date(book)
        details = format_book_details(
            book,
            weekly_pages=weekly_pages,
            monthly_pages=monthly_pages,
            avg_pages=avg_pages,
            predicted_date=pred_date,
        )
        api.messages.send(
            user_id=user_id,
            message=details,
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        context.delete_state()
