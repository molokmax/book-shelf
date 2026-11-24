"""Edit command handler as ScenarioHandler subclass.

Содержит всю логику многошагового процесса:
выбор фильтра → выбор книги → действие над книгой.
"""

from typing import Any

from vk_api.keyboard import VkKeyboard

from core.services import AchievementService, BookService
from utils import helpers, logger
from utils.helpers import format_tags_line, get_status_name
from vk_bot.context import BotContext
from vk_bot.flows.tag_editing import TagEditingFlow
from vk_bot.handlers.scenario import ScenarioHandler
from vk_bot.keyboards import (
    add_back_button,
    cancel_keyboard,
    filter_keyboard,
    status_keyboard,
    tags_keyboard,
)
from vk_bot.states import EditState
from vk_bot.user_helpers import get_or_create_user

log = logger.setup_logger(__name__)


class EditHandler(ScenarioHandler):
    """Handler for the `/edit` command.

    Управляет состояниями:
    * choose_filter → выбор фильтра (по статусу / по тегам / все)
    * selecting_status_filter → выбор статуса для фильтрации
    * selecting_tag_filter → выбор тега для фильтрации
    * selecting_book → выбор книги по номеру
    * selecting_action → выбор действия над книгой
    * editing_title, editing_author, editing_pages, editing_link
      → последовательное редактирование полей книги
    * selecting_tags → шаг выбора тегов (TagEditingFlow)
    * selecting_status → смена статуса книги
    """

    priority = 10
    commands = ["/edit", "edit"]
    scenario_command = "/edit"
    initial_state = EditState.CHOOSE_FILTER
    states = EditState

    def __init__(self) -> None:
        self._tag_flow = TagEditingFlow("/edit", self._finish_editing)

    # ── Жизненный цикл ──────────────────────────────────────────────

    def start(self, context: BotContext) -> None:
        user = get_or_create_user(context.api, context.user_id)
        self.begin(context, EditState.CHOOSE_FILTER, {"user_id": user.id})

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

    def render_selecting_action(self, context: BotContext, state_info: dict) -> None:
        title = state_info["data"].get("selected_book_title", "")
        context.send_message(
            f"Выбрана книга '{title}'. Что нужно сделать?",
            keyboard=self._create_book_keyboard(self._back_command(state_info)),
        )

    def render_editing_title(self, context: BotContext, state_info: dict) -> None:
        book = self._selected_book(state_info)
        if book is None:
            self._book_not_found(context)
            return
        context.send_message(
            (
                f"Текущее название: '{book.title}'.\n"
                "Введи новое или нажми 'Дальше' чтобы оставить."
            ),
            keyboard=self._create_edit_keyboard(self._back_command(state_info)),
        )

    def render_editing_author(self, context: BotContext, state_info: dict) -> None:
        book = self._selected_book(state_info)
        if book is None:
            self._book_not_found(context)
            return
        context.send_message(
            (
                f"Текущий автор: '{book.author}'.\n"
                "Введи нового или нажми 'Дальше' чтобы оставить."
            ),
            keyboard=self._create_edit_keyboard(self._back_command(state_info)),
        )

    def render_editing_pages(self, context: BotContext, state_info: dict) -> None:
        book = self._selected_book(state_info)
        if book is None:
            self._book_not_found(context)
            return
        context.send_message(
            (
                f"Текущее количество страниц: {book.pages}.\n"
                "Введи новое или нажми 'Дальше' чтобы оставить."
            ),
            keyboard=self._create_edit_keyboard(self._back_command(state_info)),
        )

    def render_editing_link(self, context: BotContext, state_info: dict) -> None:
        book = self._selected_book(state_info)
        if book is None:
            self._book_not_found(context)
            return
        context.send_message(
            (
                f"Текущая ссылка: {book.link or 'Отсутствует'}.\n"
                "Введи новую или нажми 'Дальше' чтобы оставить."
            ),
            keyboard=self._create_edit_keyboard(self._back_command(state_info)),
        )

    def render_selecting_status(self, context: BotContext, state_info: dict) -> None:
        title = state_info["data"].get("selected_book_title", "")
        context.send_message(
            f"📖 Выбрана книга '{title}'. Выбери новый статус:",
            keyboard=self._create_status_keyboard(self._back_command(state_info)),
        )

    def render_selecting_tags(self, context: BotContext, state_info: dict) -> None:
        """Перерисовка шага тегов после «Назад» делегируется TagEditingFlow."""
        self._tag_flow.render(context, state_info)

    # ── Шаги выбора книги ───────────────────────────────────────────

    def step_choose_filter(self, context: BotContext, state_info: dict) -> Any:
        choice = context.text.strip().lower()
        if choice == "по статусу":
            return EditState.SELECTING_STATUS_FILTER
        if choice == "по тегам":
            return EditState.SELECTING_TAG_FILTER
        if choice == "все":
            books = helpers.sort_books_by_status(
                BookService().get_all_books(self._user_id(context, state_info))
            )
            if not books:
                self.finish(context, "В библиотеке нет книг. Добавь книгу через /add")
                return None
            self._store_books(
                state_info,
                books,
                "📚 Введи номер книги для редактирования.\nБиблиотека:\n\n",
            )
            return EditState.SELECTING_BOOK

        context.send_message(
            "⚠️ Выбери: По статусу, По тегам или Все.",
            keyboard=filter_keyboard(self._back_command(state_info)),
        )
        return None

    def step_selecting_status_filter(self, context: BotContext, state_info: dict) -> Any:
        status = context.payload.get("status", "")
        books = BookService().filter_books(self._user_id(context, state_info), status=status)
        self._store_books(
            state_info,
            books,
            "📚 Введи номер книги для редактирования.\nБиблиотека:\n\n",
        )
        return EditState.SELECTING_BOOK

    def step_selecting_tag_filter(self, context: BotContext, state_info: dict) -> Any:
        selected_tag = context.text.strip()
        books = BookService().filter_books(self._user_id(context, state_info), tags=[selected_tag])
        self._store_books(
            state_info,
            books,
            "📚 Введи номер книги для редактирования.\nБиблиотека:\n\n",
        )
        return EditState.SELECTING_BOOK

    def step_selecting_book(self, context: BotContext, state_info: dict) -> Any:
        try:
            selection = int(context.text.strip())
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
        selected_book = BookService().get_book_by_id(book_id)
        if not selected_book:
            context.send_message(
                "⚠️ Книга не найдена.",
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )
            return None

        state_info["data"]["selected_book_id"] = book_id
        state_info["data"]["selected_book_title"] = selected_book.title
        return EditState.SELECTING_ACTION

    def step_selecting_action(self, context: BotContext, state_info: dict) -> Any:
        text = context.text.lower()
        data = state_info["data"]

        if text == "удалить":
            book_service = BookService()
            book_id = data.get("selected_book_id")
            if not book_id:
                context.send_message(
                    "Ошибка: идентификатор книги отсутствует.",
                    keyboard=cancel_keyboard(),
                )
                return None

            deleted_book = book_service.delete_book(book_id)
            # Финал: отправляем до delete_state, чтобы удалить висящий промпт.
            self.finish(context, f"🗑️ Книга '{deleted_book.title}' удалена.")
            return None

        if text == "статус":
            book = self._selected_book(state_info)
            if book is None:
                self._book_not_found(context)
                return None
            data["selected_book_title"] = book.title
            return EditState.SELECTING_STATUS

        if text == "изменить":
            book = self._selected_book(state_info)
            if book is None:
                self._book_not_found(context)
                return None
            return EditState.EDITING_TITLE

        context.send_message(
            "⚠️ Выбери действие",
            keyboard=self._create_book_keyboard(self._back_command(state_info)),
        )
        return None

    # ── Шаги редактирования полей ───────────────────────────────────

    def step_editing_title(self, context: BotContext, state_info: dict) -> Any:
        text = context.text
        state_info["data"]["new_title"] = None if text.lower() == "дальше" else text.strip()
        return EditState.EDITING_AUTHOR

    def step_editing_author(self, context: BotContext, state_info: dict) -> Any:
        text = context.text
        state_info["data"]["new_author"] = None if text.lower() == "дальше" else text.strip()
        return EditState.EDITING_PAGES

    def step_editing_pages(self, context: BotContext, state_info: dict) -> Any:
        text = context.text
        if text.lower() == "дальше":
            new_pages = None
        else:
            try:
                new_pages = int(text.strip())
            except ValueError:
                context.send_message(
                    "⚠️ Введи целое число для количества страниц.",
                    keyboard=self._create_edit_keyboard(self._back_command(state_info)),
                )
                return None

        state_info["data"]["new_pages"] = new_pages
        return EditState.EDITING_LINK

    def step_editing_link(self, context: BotContext, state_info: dict) -> Any:
        text = context.text
        new_link = None if text.lower() == "дальше" else text.strip()
        state_info["data"]["new_link"] = new_link

        book = self._selected_book(state_info)
        if book is None:
            self._book_not_found(context)
            return None

        # Дальше переиспользуемый шаг выбора тегов с текущими тегами книги
        self._tag_flow.start(context, state_info, preselected=book.tags)
        return None

    def step_selecting_tags(self, context: BotContext, state_info: dict) -> Any:
        """Шаг выбора тегов делегируется TagEditingFlow."""
        self._tag_flow.handle(context)
        return None

    def step_selecting_status(self, context: BotContext, state_info: dict) -> Any:
        status_map = {
            "хочу прочитать": "want_to_read",
            "читаю сейчас": "reading",
            "прочитано": "read",
            "отложено": "postponed",
        }
        new_status = status_map.get(context.text.lower())
        if not new_status:
            context.send_message(
                "⚠️ Неизвестный статус. Выбери один из предложенных.",
                keyboard=self._create_status_keyboard(self._back_command(state_info)),
            )
            return None

        book_id = state_info["data"]["selected_book_id"]
        updated_book = BookService().update_book_status(book_id, new_status)
        message_text = (
            f"✅ Статус книги '{updated_book.title}' изменён на "
            f"'{get_status_name(updated_book.status.value)}'"
        )
        user_id = self._user_id(context, state_info)
        try:
            result = AchievementService().check(user_id)
            achievement_block = helpers.format_new_achievements(result.new_achievements)
            if achievement_block:
                message_text = f"{message_text}\n\n{achievement_block}"
        except Exception as error:
            log.error("Failed to check achievements after changing book status: %s", error)

        self.finish(context, message_text)
        return None

    # ── Финал ───────────────────────────────────────────────────────

    def _finish_editing(self, context: BotContext, tags: list[str]) -> None:
        """Завершение шага тегов в /edit: применяет накопленные поля и теги."""
        state_info = context.get_state()
        data = state_info["data"]

        book_id = data["selected_book_id"]
        book_service = BookService()
        book = book_service.get_book_by_id(book_id)
        if not book:
            self.finish(context, "⚠️ Книга не найдена.")
            return

        if data.get("new_title") is not None:
            book.title = data["new_title"]
        if data.get("new_author") is not None:
            book.author = data["new_author"]
        if data.get("new_pages") is not None:
            book.pages = data["new_pages"]
        if data.get("new_link") is not None:
            book.link = data["new_link"]
        book.tags = tags
        book_service.book_repo.update_book(book)
        self.finish(
            context,
            (
                f"✅ Книга обновлена: '{book.title}' от {book.author}.\n"
                f"Теги: {format_tags_line(tags)}"
            ),
        )

    # ── Данные и служебные методы ───────────────────────────────────

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
    def _selected_book(state_info: dict):
        book_id = state_info.get("data", {}).get("selected_book_id")
        if not book_id:
            return None
        return BookService().get_book_by_id(book_id)

    @staticmethod
    def _book_not_found(context: BotContext) -> None:
        context.send_message("⚠️ Книга не найдена.", keyboard=cancel_keyboard())

    @staticmethod
    def _user_id(context: BotContext, state_info: dict) -> str:
        user_id = state_info.get("data", {}).get("user_id")
        if not user_id:
            user = get_or_create_user(context.api, context.user_id)
            user_id = user.id
            state_info.setdefault("data", {})["user_id"] = user_id
            context.set_state(state_info)
        return user_id

    # ── Клавиатуры ──────────────────────────────────────────────────

    @staticmethod
    def _create_book_keyboard(back_command: str | None = None) -> VkKeyboard:
        """Клавиатура действий над книгой."""
        kb = VkKeyboard()
        kb.add_button("Изменить")
        kb.add_button("Статус")
        kb.add_line()
        kb.add_button("Удалить")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        add_back_button(kb, back_command)
        return kb

    @staticmethod
    def _create_status_keyboard(back_command: str | None = None) -> VkKeyboard:
        """Создаёт клавиатуру для выбора нового статуса книги без payload."""
        kb = VkKeyboard()
        kb.add_button("Хочу прочитать")
        kb.add_button("Читаю сейчас")
        kb.add_line()
        kb.add_button("Прочитано")
        kb.add_button("Отложено")
        kb.add_line()
        kb.add_button("Отмена", payload={"command": "/cancel"})
        add_back_button(kb, back_command)
        return kb

    @staticmethod
    def _create_edit_keyboard(back_command: str | None = None) -> VkKeyboard:
        """Keyboard with 'Дальше' and 'Отмена' for sequential editing."""
        kb = VkKeyboard()
        kb.add_button("Дальше")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        add_back_button(kb, back_command)
        return kb
