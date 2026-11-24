"""Add command handler.

Содержит всю логику обработки команды /add: входную точку,
шаги сценария, переиспользуемый шаг выбора тегов и фабрики клавиатур.
"""

from typing import Any

from vk_api.keyboard import VkKeyboard

from core.services import AchievementService, BookService
from utils import helpers, logger
from utils.helpers import format_tags_line
from utils.litres_parser import LitresParserError, is_litres_url, parse_litres_book
from vk_bot.context import BotContext
from vk_bot.flows.tag_editing import TagEditingFlow
from vk_bot.handlers.scenario import ScenarioHandler
from vk_bot.keyboards import add_back_button, cancel_keyboard
from vk_bot.states import AddState
from vk_bot.user_helpers import get_or_create_user

log = logger.setup_logger(__name__)


class AddHandler(ScenarioHandler):
    """Handler for the `/add` command."""

    priority = 10
    commands = ["/add", "add"]
    scenario_command = "/add"
    initial_state = AddState.CHOOSE_METHOD
    states = AddState

    def __init__(self) -> None:
        self._tag_flow = TagEditingFlow("/add", self._finish_with_book)

    # ── Жизненный цикл ──────────────────────────────────────────────

    def start(self, context: BotContext) -> None:
        self.begin(context, AddState.CHOOSE_METHOD, {})

    def render_choose_method(self, context: BotContext, state_info: dict) -> None:
        context.send_message(
            "➕ Добавление новой книги. Выбери способ добавления:",
            keyboard=self.create_add_method_keyboard(),
        )

    def render_waiting_for_title(self, context: BotContext, state_info: dict) -> None:
        context.send_message(
            "Отлично! Теперь введи название книги:",
            keyboard=cancel_keyboard(self._back_command(state_info)),
        )

    def render_waiting_for_author(self, context: BotContext, state_info: dict) -> None:
        context.send_message(
            "Отлично! Теперь введи автора книги:",
            keyboard=cancel_keyboard(self._back_command(state_info)),
        )

    def render_waiting_for_pages(self, context: BotContext, state_info: dict) -> None:
        context.send_message(
            "Отлично! Теперь введи количество страниц в книге:",
            keyboard=cancel_keyboard(self._back_command(state_info)),
        )

    def render_waiting_for_link(self, context: BotContext, state_info: dict) -> None:
        context.send_message(
            (
                "Отлично! Теперь можешь указать ссылку на книгу. "
                "Нажми Дальше чтобы оставить пустым."
            ),
            keyboard=self.create_link_keyboard(self._back_command(state_info)),
        )

    def render_waiting_for_litres_url(self, context: BotContext, state_info: dict) -> None:
        context.send_message(
            "Введи ссылку на книгу с https://litres.ru:",
            keyboard=cancel_keyboard(self._back_command(state_info)),
        )

    def render_waiting_for_litres_confirm(self, context: BotContext, state_info: dict) -> None:
        data = state_info["data"]
        context.send_message(
            (
                f"✅ Найдены данные книги:\n"
                f"\nНазвание: {data.get('title', '—')}\n"
                f"Автор: {data.get('author', '—')}\n"
                f"Страниц: {data.get('pages', '—')}\n"
                "\nПродолжить добавление?"
            ),
            keyboard=self.create_confirm_litres_keyboard(self._back_command(state_info)),
        )

    def render_selecting_tags(self, context: BotContext, state_info: dict) -> None:
        """Перерисовка шага тегов после «Назад» делегируется TagEditingFlow."""
        self._tag_flow.render(context, state_info)

    # ── Шаги ────────────────────────────────────────────────────────

    def step_choose_method(self, context: BotContext, state_info: dict) -> Any:
        text = context.text.strip()

        if text == "Ручное":
            return AddState.WAITING_FOR_TITLE
        if text == "Из LitRes":
            return AddState.WAITING_FOR_LITRES_URL

        context.send_message(
            "Пожалуйста, выбери: Ручное или Из LitRes.",
            keyboard=self.create_add_method_keyboard(),
        )
        return None

    def step_waiting_for_title(self, context: BotContext, state_info: dict) -> Any:
        state_info["data"]["title"] = context.text.strip()
        return AddState.WAITING_FOR_AUTHOR

    def step_waiting_for_author(self, context: BotContext, state_info: dict) -> Any:
        state_info["data"]["author"] = context.text.strip()
        return AddState.WAITING_FOR_PAGES

    def step_waiting_for_pages(self, context: BotContext, state_info: dict) -> Any:
        text = context.text.strip()

        try:
            pages = int(text)
            if pages <= 0:
                raise ValueError
        except ValueError:
            context.send_message(
                "⚠️ Введи положительное целое число страниц.",
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )
            return None

        state_info["data"]["pages"] = pages
        return AddState.WAITING_FOR_LINK

    def step_waiting_for_link(self, context: BotContext, state_info: dict) -> Any:
        text = context.text.strip()

        if not text or text.lower() == "дальше":
            state_info["data"]["link"] = None
        else:
            if not helpers.is_valid_url(text):
                context.send_message(
                    "⚠️ Введи корректный URL или нажми 'Дальше'.",
                    keyboard=self.create_link_keyboard(self._back_command(state_info)),
                )
                return None
            state_info["data"]["link"] = text

        # Дальше переиспользуемый шаг выбора тегов
        self._tag_flow.start(context, state_info, preselected=[])
        return None

    def step_selecting_tags(self, context: BotContext, state_info: dict) -> Any:
        """Шаг выбора тегов делегируется TagEditingFlow."""
        self._tag_flow.handle(context)
        return None

    def step_waiting_for_litres_url(self, context: BotContext, state_info: dict) -> Any:
        url = context.text.strip()
        data = state_info["data"]

        if not is_litres_url(url):
            context.send_message(
                "⚠️ Введи корректную ссылку на LitRes.",
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )
            return None

        try:
            book_data = parse_litres_book(url)
            if (
                not book_data.get("title")
                or not book_data.get("author")
                or not book_data.get("pages")
            ):
                raise LitresParserError("Недостаточно данных о книге")

            data.update(
                {
                    "title": book_data["title"],
                    "author": book_data["author"],
                    "pages": book_data["pages"],
                    "link": url,
                }
            )
            return AddState.WAITING_FOR_LITRES_CONFIRM
        except LitresParserError as e:
            context.send_message(
                f"❌ Не удалось получить информацию о книге: {e}",
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )
            return None

    def step_waiting_for_litres_confirm(self, context: BotContext, state_info: dict) -> Any:
        if context.text.strip() == "Продолжить":
            # Дальше переиспользуемый шаг выбора тегов
            self._tag_flow.start(context, state_info, preselected=[])
        return None

    # ── Финал ───────────────────────────────────────────────────────

    def _finish_with_book(self, context: BotContext, tags: list[str]) -> None:
        """Завершение шага тегов в /add: создаёт книгу с итоговой выборкой."""
        api = context.api
        user_id = context.user_id
        data = context.get_state()["data"]

        user = get_or_create_user(api, user_id)
        book = BookService().create_book(
            title=data["title"],
            author=data["author"],
            tags=tags,
            pages=data["pages"],
            user_id=user.id,
            link=data.get("link"),
        )
        message_text = (
            f"✅ Книга '{book.title}' успешно добавлена в твою библиотеку!\n"
            f"\nТеги: {format_tags_line(tags)}\n"
            "\nТы можешь\n"
            "/add - Добавить ещё одну книгу\n"
            "/list - Показать список книг"
        )
        try:
            result = AchievementService().check(user.id)
            achievement_block = helpers.format_new_achievements(result.new_achievements)
            if achievement_block:
                message_text = f"{message_text}\n\n{achievement_block}"
        except Exception as error:
            log.error("Failed to check achievements after adding a book: %s", error)

        self.finish(context, message_text, keyboard=self.create_book_added_keyboard())

    # ── Фабрики клавиатур ──────────────────────────────────────────

    @staticmethod
    def create_book_added_keyboard() -> VkKeyboard:
        kb = VkKeyboard()
        kb.add_button("/add")
        kb.add_button("/list")
        kb.add_line()
        kb.add_button("Главное меню", payload={"command": "/back"})
        return kb

    @staticmethod
    def create_add_method_keyboard() -> VkKeyboard:
        kb = VkKeyboard()
        kb.add_button("Ручное", payload={"command": "/add_manual"})
        kb.add_button("Из LitRes", payload={"command": "/add_litres"})
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb

    @staticmethod
    def create_link_keyboard(back_command: str | None = None) -> VkKeyboard:
        kb = VkKeyboard()
        kb.add_button("Дальше")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        add_back_button(kb, back_command)
        return kb

    @staticmethod
    def create_confirm_litres_keyboard(back_command: str | None = None) -> VkKeyboard:
        kb = VkKeyboard()
        kb.add_button("Продолжить")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        add_back_button(kb, back_command)
        return kb
