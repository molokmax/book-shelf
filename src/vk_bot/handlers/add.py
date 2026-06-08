"""Add command handler.

Содержит всю логику обработки команды /add: входную точку,
стейт-машину с диспетчеризацией по state и фабрики клавиатур.
"""

from typing import Any

from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id

from core.services import BookService
from utils import helpers
from utils.litres_parser import (LitresParserError, is_litres_url,
                                 parse_litres_book)
from vk_bot.keyboards import cancel_keyboard, main_keyboard
from vk_bot.user_helpers import get_or_create_user

from ..context import BotContext
from .base import AbstractCommandHandler


class AddHandler(AbstractCommandHandler):
    """Handler for the `/add` command."""

    priority = 10
    commands = ["/add", "add"]

    _STATE_DISPATCH = {}

    def handle(self, context: BotContext) -> Any:
        if context.is_active():
            self._handle_step(context)
        else:
            self._handle_start(context)
        return True

    # ── Входная точка ──────────────────────────────────────────────

    def _handle_start(self, context: BotContext) -> None:
        api = context.api
        user_id = context.user_id
        context.set_state({"command": "/add", "state": "choose_method", "data": {}})
        api.messages.send(
            user_id=user_id,
            message="➕ Добавление новой книги. Выбери способ добавления:",
            keyboard=self.create_add_method_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    # ── Диспетчер шагов ─────────────────────────────────────────────

    def _handle_step(self, context: BotContext) -> None:
        if not context.is_active():
            return

        state_info = context.get_state()
        state = state_info.get("state")

        handler = self._STATE_DISPATCH.get(state)
        if handler is not None:
            handler(self, context, state_info)
        else:
            context.delete_state()
            context.api.messages.send(
                user_id=context.user_id,
                message=("Добавление книги сброшено. Повтори команду /add."),
                keyboard=main_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )

    # ── Обработчики состояний ──────────────────────────────────────

    def _handle_choose_method(self, context: BotContext, state_info: dict) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text.strip()

        if text == "Ручное":
            state_info["state"] = "waiting_for_title"
            context.set_state(state_info)
            api.messages.send(
                user_id=user_id,
                message="Отлично! Теперь введи название книги:",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
        elif text == "Из LitRes":
            state_info["state"] = "waiting_for_litres_url"
            context.set_state(state_info)
            api.messages.send(
                user_id=user_id,
                message="Введи ссылку на книгу с https://litres.ru:",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
        else:
            api.messages.send(
                user_id=user_id,
                message="Пожалуйста, выбери: Ручное или Из LitRes.",
                keyboard=self.create_add_method_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )

    def _handle_waiting_for_title(self, context: BotContext, state_info: dict) -> None:
        state_info["data"]["title"] = context.text.strip()
        state_info["state"] = "waiting_for_author"
        context.set_state(state_info)
        context.api.messages.send(
            user_id=context.user_id,
            message="Отлично! Теперь введи автора книги:",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_waiting_for_author(self, context: BotContext, state_info: dict) -> None:
        state_info["data"]["author"] = context.text.strip()
        state_info["state"] = "waiting_for_pages"
        context.set_state(state_info)
        context.api.messages.send(
            user_id=context.user_id,
            message="Отлично! Теперь введи количество страниц в книге:",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_waiting_for_pages(self, context: BotContext, state_info: dict) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text.strip()

        try:
            pages = int(text)
            if pages <= 0:
                raise ValueError
        except ValueError:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Введи положительное целое число страниц.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        state_info["data"]["pages"] = pages
        state_info["state"] = "waiting_for_link"
        context.set_state(state_info)
        api.messages.send(
            user_id=user_id,
            message=(
                "Отлично! Теперь можешь указать ссылку на книгу. "
                "Нажми Дальше чтобы оставить пустым."
            ),
            keyboard=self.create_link_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_waiting_for_link(self, context: BotContext, state_info: dict) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text.strip()

        if not text or text.lower() == "дальше":
            state_info["data"]["link"] = None
        else:
            if not helpers.is_valid_url(text):
                api.messages.send(
                    user_id=user_id,
                    message="⚠️ Введи корректный URL или нажми 'Дальше'.",
                    keyboard=self.create_link_keyboard().get_keyboard(),
                    random_id=get_random_id(),
                )
                return
            state_info["data"]["link"] = text

        state_info["state"] = "waiting_for_tags"
        context.set_state(state_info)
        api.messages.send(
            user_id=user_id,
            message=(
                "Хорошо! Теперь введи теги книги через запятую "
                "(например: Tech, Программирование):"
            ),
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_waiting_for_tags(self, context: BotContext, state_info: dict) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text.strip()
        data = state_info["data"]

        tags = [tag.strip() for tag in text.split(",") if tag.strip()]
        data["tags"] = tags

        user = get_or_create_user(api, user_id)
        book_service = BookService()
        book = book_service.create_book(
            title=data["title"],
            author=data["author"],
            tags=data["tags"],
            pages=data["pages"],
            user_id=user.id,
            link=data.get("link"),
        )
        context.delete_state()
        message_text = (
            f"✅ Книга '{book.title}' успешно добавлена в твою библиотеку!\n"
            "\nТы можешь\n"
            "/add - Добавить ещё одну книгу\n"
            "/list - Показать список книг"
        )
        api.messages.send(
            user_id=user_id,
            message=message_text,
            keyboard=self.create_book_added_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_waiting_for_litres_url(
        self, context: BotContext, state_info: dict
    ) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text.strip()
        data = state_info["data"]

        url = text.strip()
        if not is_litres_url(url):
            api.messages.send(
                user_id=user_id,
                message="⚠️ Введи корректную ссылку на LitRes.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

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
                }
            )
            data["link"] = url
            state_info["state"] = "waiting_for_litres_confirm"
            context.set_state(state_info)
            api.messages.send(
                user_id=user_id,
                message=(
                    f"✅ Найдены данные книги:\n"
                    f"\nНазвание: {book_data.get('title', '—')}\n"
                    f"Автор: {book_data.get('author', '—')}\n"
                    f"Страниц: {book_data.get('pages', '—')}\n"
                    "\nПродолжить добавление?"
                ),
                keyboard=self.create_confirm_litres_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
        except LitresParserError as e:
            api.messages.send(
                user_id=user_id,
                message=f"❌ Не удалось получить информацию о книге: {e}",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )

    def _handle_waiting_for_litres_confirm(
        self, context: BotContext, state_info: dict
    ) -> None:
        text = context.text.strip()
        if text == "Продолжить":
            state_info["state"] = "waiting_for_litres_tags"
            context.set_state(state_info)
            context.api.messages.send(
                user_id=context.user_id,
                message=(
                    "Отлично! Теперь введи теги книги через запятую "
                    "(например: Tech, Программирование):"
                ),
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )

    def _handle_waiting_for_litres_tags(
        self, context: BotContext, state_info: dict
    ) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text.strip()
        data = state_info["data"]

        tags = [tag.strip() for tag in text.split(",") if tag.strip()]
        data["tags"] = tags

        user = get_or_create_user(api, user_id)
        book_service = BookService()
        book = book_service.create_book(
            title=data["title"],
            author=data["author"],
            tags=data["tags"],
            pages=data["pages"],
            user_id=user.id,
            link=data["link"],
        )
        context.delete_state()
        message_text = (
            f"✅ Книга '{book.title}' успешно добавлена!\n"
            "\nТы можешь\n"
            "/add - Добавить ещё одну книгу\n"
            "/list - Показать список книг"
        )
        api.messages.send(
            user_id=user_id,
            message=message_text,
            keyboard=self.create_book_added_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    # ── Фабрики клавиатур ──────────────────────────────────────────

    @staticmethod
    def create_book_added_keyboard() -> VkKeyboard:
        kb = VkKeyboard()
        kb.add_button("/add")
        kb.add_button("/list")
        return kb

    @staticmethod
    def create_add_method_keyboard() -> VkKeyboard:
        kb = VkKeyboard()
        kb.add_button("Ручное", payload={"command": "/add_manual"})
        kb.add_button("Из LitRes", payload={"command": "/add_litres"})
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb

    @staticmethod
    def create_link_keyboard() -> VkKeyboard:
        kb = VkKeyboard()
        kb.add_button("Дальше")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb

    @staticmethod
    def create_confirm_litres_keyboard() -> VkKeyboard:
        kb = VkKeyboard()
        kb.add_button("Продолжить")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb


AddHandler._STATE_DISPATCH = {
    "choose_method": AddHandler._handle_choose_method,
    "waiting_for_title": AddHandler._handle_waiting_for_title,
    "waiting_for_author": AddHandler._handle_waiting_for_author,
    "waiting_for_pages": AddHandler._handle_waiting_for_pages,
    "waiting_for_link": AddHandler._handle_waiting_for_link,
    "waiting_for_tags": AddHandler._handle_waiting_for_tags,
    "waiting_for_litres_url": AddHandler._handle_waiting_for_litres_url,
    "waiting_for_litres_confirm": AddHandler._handle_waiting_for_litres_confirm,
    "waiting_for_litres_tags": AddHandler._handle_waiting_for_litres_tags,
}
