"""Обработчик команды /progress: быстрое обновление прогресса чтения."""

from typing import Any

from vk_api.keyboard import VkKeyboard

from core.models import ReadingStatus
from core.services import BookService
from core.storage import ActiveStateStorage
from utils import helpers
from vk_bot.context import BotContext
from vk_bot.flows.book_selection import BookSelectionFlow
from vk_bot.flows.progress_update import ProgressUpdateFlow
from vk_bot.handlers.scenario import ScenarioHandler
from vk_bot.states import ProgressScenarioState
from vk_bot.user_helpers import get_or_create_user


class ProgressHandler(ScenarioHandler):
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
    scenario_command = "/progress"
    initial_state = ProgressScenarioState.SELECTING_READING_BOOK
    states = ProgressScenarioState

    def __init__(self) -> None:
        self._progress = ProgressUpdateFlow()
        self._selection = BookSelectionFlow(on_selected=self._on_book_selected)

    # ── Жизненный цикл ──────────────────────────────────────────────

    def start(self, context: BotContext) -> None:
        user = get_or_create_user(context.api, context.user_id)
        state_info = ActiveStateStorage.new_state(
            self.scenario_command,
            str(ProgressScenarioState.SELECTING_READING_BOOK),
            {"user_id": user.id},
        )
        self._show_reading_books(context, state_info)

    def render_selecting_reading_book(self, context: BotContext, state_info: dict) -> None:
        data = state_info["data"]
        context.send_message(
            data["list_header"] + "".join(data["book_lines"]),
            keyboard=self._create_reading_keyboard(),
        )

    # ── Шаги ────────────────────────────────────────────────────────

    def step_selecting_reading_book(self, context: BotContext, state_info: dict) -> Any:
        text = context.text.strip()

        if text.lower() == "другие":
            self._selection.start(context, state_info, "Какие книги интересуют?")
            return None

        try:
            selection = int(text)
        except ValueError:
            context.send_message(
                helpers.format_invalid_input("Введи корректный номер книги."),
                keyboard=self._create_reading_keyboard(),
            )
            return None

        books_ids = state_info["data"].get("books", [])
        if selection < 1 or selection > len(books_ids):
            context.send_message(
                helpers.format_invalid_input("Номер книги вне диапазона."),
                keyboard=self._create_reading_keyboard(),
            )
            return None

        book = BookService().get_book_by_id(books_ids[selection - 1])
        if not book:
            context.send_message(
                "⚠️ Книга не найдена.",
                keyboard=self._create_reading_keyboard(),
            )
            return None

        self._on_book_selected(context, book)
        return None

    def step_choose_filter(self, context: BotContext, state_info: dict) -> Any:
        self._selection.handle(context)
        return None

    def step_selecting_status_filter(self, context: BotContext, state_info: dict) -> Any:
        self._selection.handle(context)
        return None

    def step_selecting_tag_filter(self, context: BotContext, state_info: dict) -> Any:
        self._selection.handle(context)
        return None

    def step_selecting_book(self, context: BotContext, state_info: dict) -> Any:
        self._selection.handle(context)
        return None

    def step_waiting_for_progress_input(self, context: BotContext, state_info: dict) -> Any:
        self._progress.handle(context)
        return None

    def step_waiting_for_progress_confirm(self, context: BotContext, state_info: dict) -> Any:
        self._progress.handle(context)
        return None

    # ── Данные ──────────────────────────────────────────────────────

    def _show_reading_books(self, context: BotContext, state_info: dict) -> None:
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
        state_info["data"]["books"] = [book.id for book in books]
        state_info["data"][
            "list_header"
        ] = "📚 Введи номер книги для обновления прогресса.\nКниги в статусе «Читаю»:\n\n"
        state_info["data"]["book_lines"] = [
            helpers.format_book_info(i, book) + "\n" for i, book in enumerate(books, 1)
        ]
        self.goto(context, ProgressScenarioState.SELECTING_READING_BOOK, state_info)

    def _on_book_selected(self, context: BotContext, book) -> None:
        state_info = context.get_state()
        state_info["data"]["selected_book_id"] = book.id
        self._progress.start(context, state_info, book)

    @staticmethod
    def _create_reading_keyboard() -> VkKeyboard:
        """Клавиатура выбора книги из статуса «Читаю»."""
        kb = VkKeyboard()
        kb.add_button("Другие")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb
