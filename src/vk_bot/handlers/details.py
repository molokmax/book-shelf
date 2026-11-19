"""Обработчик команды /details.

Содержит всю логику многошагового процесса:
выбор фильтра → выбор книги → показ деталей.
"""

from datetime import datetime, timedelta
from typing import Any

from core.services import BookService, ReadingStatsService, UserSettingsService
from utils import helpers
from utils.helpers import format_book_details
from vk_bot.context import BotContext
from vk_bot.handlers.scenario import ScenarioHandler
from vk_bot.keyboards import cancel_keyboard, filter_keyboard, status_keyboard, tags_keyboard
from vk_bot.states import DetailsState
from vk_bot.user_helpers import get_or_create_user


class DetailsHandler(ScenarioHandler):
    """Handler for the `/details` command.

    Управляет состояниями:
    * choose_filter → выбор фильтра (по статусу / по тегам / все)
    * selecting_status_filter → выбор статуса
    * selecting_tag_filter → выбор тега
    * selecting_book → выбор книги и показ деталей
    """

    priority = 10
    commands = ["/details", "details"]
    scenario_command = "/details"
    initial_state = DetailsState.CHOOSE_FILTER
    states = DetailsState

    # ── Жизненный цикл ──────────────────────────────────────────────

    def start(self, context: BotContext) -> None:
        user = get_or_create_user(context.api, context.user_id)
        self.begin(context, DetailsState.CHOOSE_FILTER, {"user_id": user.id})

    def render_choose_filter(self, context: BotContext, state_info: dict) -> None:
        context.send_message(
            "Какие книги интересуют?",
            keyboard=filter_keyboard(self._back_command(state_info)),
        )

    def render_selecting_status_filter(self, context: BotContext, state_info: dict) -> None:
        context.send_message(
            "Выбери статус книги:",
            keyboard=status_keyboard(self._back_command(state_info)),
        )

    def render_selecting_tag_filter(self, context: BotContext, state_info: dict) -> None:
        tags = BookService().get_all_tags(self._user_id(context, state_info))
        context.send_message(
            "Выбери тег:",
            keyboard=tags_keyboard(tags, self._back_command(state_info)),
        )

    def render_selecting_book(self, context: BotContext, state_info: dict) -> None:
        data = state_info["data"]
        context.send_message(
            data["list_header"] + "".join(data["book_lines"]),
            keyboard=cancel_keyboard(self._back_command(state_info)),
        )

    # ── Шаги ────────────────────────────────────────────────────────

    def step_choose_filter(self, context: BotContext, state_info: dict) -> Any:
        choice = context.text.strip().lower()
        if choice == "по статусу":
            return DetailsState.SELECTING_STATUS_FILTER
        if choice == "по тегам":
            return DetailsState.SELECTING_TAG_FILTER
        if choice == "все":
            books = helpers.sort_books_by_status(
                BookService().get_all_books(self._user_id(context, state_info))
            )
            if not books:
                # Финал (пустой результат): отправляем до delete_state.
                self.finish(context, "В библиотеке нет книг. Добавь книгу через /add")
                return None
            self._store_books(state_info, books, "📚 Введи номер книги.\nТвоя библиотека:\n\n")
            return DetailsState.SELECTING_BOOK

        context.send_message(
            "⚠️ Выбери: По статусу, По тегам или Все",
            keyboard=filter_keyboard(self._back_command(state_info)),
        )
        return None

    def step_selecting_status_filter(self, context: BotContext, state_info: dict) -> Any:
        status = context.payload.get("status", "")
        books = helpers.sort_books_by_status(
            BookService().filter_books(self._user_id(context, state_info), status=status)
        )
        if not books:
            # Финал (пустой результат): отправляем до delete_state.
            self.finish(context, "Книг с выбранным статусом нет.")
            return None
        self._store_books(
            state_info,
            books,
            "📚 Введи номер книги.\nКниги с выбранным статусом:\n\n",
        )
        return DetailsState.SELECTING_BOOK

    def step_selecting_tag_filter(self, context: BotContext, state_info: dict) -> Any:
        selected_tag = context.text.strip()
        books = helpers.sort_books_by_status(
            BookService().filter_books(self._user_id(context, state_info), tags=[selected_tag])
        )
        if not books:
            # Финал (пустой результат): отправляем до delete_state.
            self.finish(context, "Книг с выбранным тегом нет.")
            return None
        self._store_books(
            state_info,
            books,
            "📚 Введи номер книги.\nКниги с выбранным тегом:\n\n",
        )
        return DetailsState.SELECTING_BOOK

    def step_selecting_book(self, context: BotContext, state_info: dict) -> Any:
        text = context.text

        try:
            selection = int(text.strip())
        except ValueError:
            context.send_message(
                "⚠️ Введи корректный номер книги.",
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )
            return None

        books_ids = state_info["data"]["books"]
        if selection < 1 or selection > len(books_ids):
            context.send_message(
                "⚠️ Номер книги вне диапазона.",
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )
            return None

        book_id = books_ids[selection - 1]
        book = BookService().get_book_by_id(book_id)
        if not book:
            context.send_message(
                "⚠️ Книга не найдена.",
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )
            return None

        stats_service = ReadingStatsService()
        # Период берём по внутреннему идентификатору пользователя из состояния.
        settings_user_id = state_info["data"].get("user_id")
        period_days = UserSettingsService().get_reading_speed_period(settings_user_id)
        today = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        week_start = (today - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = (today - timedelta(days=30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        weekly_pages = stats_service.get_reading_stats(book.id, week_start, today)
        monthly_pages = stats_service.get_reading_stats(book.id, month_start, today)
        avg_pages = stats_service.avg_pages_per_day(book)
        days_left = stats_service.predict_days_to_completion(book)
        pred_date = stats_service.predict_completion_date(book)
        details = format_book_details(
            book,
            weekly_pages=weekly_pages,
            monthly_pages=monthly_pages,
            avg_pages=avg_pages,
            days_to_completion=days_left,
            predicted_date=pred_date,
            period_days=period_days,
        )
        self.finish(context, details)
        return None

    # ── Данные ──────────────────────────────────────────────────────

    @staticmethod
    def _store_books(state_info: dict, books: list, header: str) -> None:
        """Запоминает книги для шага выбора, чтобы не читать их повторно."""
        data = state_info["data"]
        data["books"] = [book.id for book in books]
        data["list_header"] = header
        data["book_lines"] = [
            helpers.format_book_info(i, book) + "\n" for i, book in enumerate(books, 1)
        ]

    @staticmethod
    def _user_id(context: BotContext, state_info: dict) -> str:
        user_id = state_info.get("data", {}).get("user_id")
        if not user_id:
            user = get_or_create_user(context.api, context.user_id)
            user_id = user.id
            state_info.setdefault("data", {})["user_id"] = user_id
            context.set_state(state_info)
        return user_id
