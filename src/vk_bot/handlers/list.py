"""List command handler as ScenarioHandler subclass."""

from typing import Any

from core.services import BookService
from utils import helpers
from vk_bot.context import BotContext
from vk_bot.handlers.scenario import ScenarioHandler
from vk_bot.keyboards import filter_keyboard, status_keyboard, tags_keyboard
from vk_bot.states import ListState
from vk_bot.user_helpers import get_or_create_user


class ListHandler(ScenarioHandler):
    priority = 10
    commands = ["/list", "list"]
    scenario_command = "/list"
    initial_state = ListState.CHOOSE_FILTER
    states = ListState

    # ── Жизненный цикл ──────────────────────────────────────────────

    def start(self, context: BotContext) -> None:
        user = get_or_create_user(context.api, context.user_id)
        self.begin(context, ListState.CHOOSE_FILTER, {"user_id": user.id})

    def render_choose_filter(self, context: BotContext, state_info: dict) -> None:
        context.send_message(
            "Какие книги интересуют?",
            keyboard=filter_keyboard(),
        )

    def render_choose_status(self, context: BotContext, state_info: dict) -> None:
        context.send_message(
            "Выбери статус книги:",
            keyboard=status_keyboard(),
        )

    def render_choose_tag(self, context: BotContext, state_info: dict) -> None:
        tags = BookService().get_all_tags(self._user_id(context, state_info))
        context.send_message(
            "Выбери тег:",
            keyboard=tags_keyboard(tags),
        )

    # ── Шаги ────────────────────────────────────────────────────────

    def step_choose_filter(self, context: BotContext, state_info: dict) -> Any:
        choice = context.text.strip().lower()
        if choice == "по статусу":
            return ListState.CHOOSE_STATUS
        if choice == "по тегам":
            return ListState.CHOOSE_TAG
        if choice == "все":
            books = helpers.sort_books_by_status(
                BookService().get_all_books(self._user_id(context, state_info))
            )
            if not books:
                self.finish(context, "Твоя библиотека пуста. Добавь книгу через /add")
                return None
            lines = ["📚 Твоя библиотека:\n\n"]
            for i, book in enumerate(books, 1):
                lines.append(helpers.format_book_info(i, book) + "\n")
            self.finish(context, "".join(lines))
            return None

        context.send_message(
            "Выбери: По статусу, По тегам, Все или Отмена.",
            keyboard=filter_keyboard(),
        )
        return None

    def step_choose_status(self, context: BotContext, state_info: dict) -> Any:
        status = context.payload.get("status", "")
        books = helpers.sort_books_by_status(
            BookService().filter_books(self._user_id(context, state_info), status=status)
        )
        if not books:
            self.finish(context, "Книг с выбранным статусом нет.")
            return None
        lines = [f"📚 Книги со статусом '{helpers.get_status_name(status)}':\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        self.finish(context, "".join(lines))
        return None

    def step_choose_tag(self, context: BotContext, state_info: dict) -> Any:
        text = context.text.strip()
        books = helpers.sort_books_by_status(
            BookService().filter_books(self._user_id(context, state_info), tags=[text])
        )
        if not books:
            self.finish(context, f"Книг с тегом '{text}' нет.")
            return None
        lines = [f"📚 Книги с тегом '{text}':\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        self.finish(context, "".join(lines))
        return None

    # ── Данные ──────────────────────────────────────────────────────

    @staticmethod
    def _user_id(context: BotContext, state_info: dict) -> str:
        user_id = state_info.get("data", {}).get("user_id")
        if not user_id:
            user = get_or_create_user(context.api, context.user_id)
            user_id = user.id
            state_info.setdefault("data", {})["user_id"] = user_id
            context.set_state(state_info)
        return user_id
