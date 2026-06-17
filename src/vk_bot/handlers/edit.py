"""Edit command handler as AbstractCommandHandler subclass.

Содержит всю логику многошагового процесса:
выбор фильтра → выбор книги → действие над книгой.
"""

from typing import Any

from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id

from core.services import BookService
from utils import helpers, logger
from utils.helpers import get_status_name
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


class EditHandler(AbstractCommandHandler):
    """Handler for the `/edit` command.

    Управляет состояниями:
    * choose_filter → выбор фильтра (по статусу / по тегам / все)
    * selecting_status_filter → выбор статуса для фильтрации
    * selecting_tag_filter → выбор тега для фильтрации
    * selecting_book → выбор книги по номеру
    * selecting_action → выбор действия над книгой
    * editing_title, editing_author, editing_pages, editing_link, editing_tags
      → последовательное редактирование полей книги
    * selecting_status → смена статуса книги
    * waiting_for_progress_input → обновление прогресса чтения
    """

    priority = 10
    commands = ["/edit", "edit"]

    def handle(self, context: BotContext) -> Any:
        if not context.is_active():
            self._handle_entry(context)
            return True

        state_info = context.get_state()
        if not state_info or state_info.get("command") != "/edit":
            return True

        state = state_info.get("state")
        if state == "choose_filter":
            self._handle_choose_filter(context)
        elif state == "selecting_book":
            self._handle_selecting_book(context)
        elif state == "selecting_action":
            self._handle_selecting_action(context)
        elif state == "selecting_status_filter":
            self._handle_selecting_status_filter(context)
        elif state == "selecting_tag_filter":
            self._handle_selecting_tag_filter(context)
        elif state == "editing_title":
            self._handle_editing_title(context)
        elif state == "editing_author":
            self._handle_editing_author(context)
        elif state == "editing_pages":
            self._handle_editing_pages(context)
        elif state == "editing_link":
            self._handle_editing_link(context)
        elif state == "editing_tags":
            self._handle_editing_tags(context)
        elif state == "selecting_status":
            self._handle_selecting_status(context)
        elif state == "waiting_for_progress_input":
            self._handle_waiting_for_progress_input(context)

        return True

    def _handle_entry(self, context) -> None:
        api = context.api
        user_id = context.user_id
        user = get_or_create_user(api, user_id)
        context.set_state(
            {
                "command": "/edit",
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
            state_info["data"]["filter_mode"] = "status"
            state_info["state"] = "selecting_status_filter"
            context.set_state(state_info)
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
            state_info["data"]["filter_mode"] = "tags"
            state_info["state"] = "selecting_tag_filter"
            context.set_state(state_info)
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

            context.set_state(
                {
                    "command": "/edit",
                    "state": "selecting_book",
                    "data": {"books": [book.id for book in books]},
                }
            )
            lines = ["📚 Введи номер книги для редактирования.\nБиблиотека:\n\n"]
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
            message="⚠️ Выбери: По статусу, По тегам или Все.",
            keyboard=filter_keyboard().get_keyboard(),
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
        book_service = BookService()
        selected_book = book_service.get_book_by_id(book_id)
        if not selected_book:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        state_info["state"] = "selecting_action"
        state_info["data"]["selected_book_id"] = book_id
        context.set_state(state_info)
        api.messages.send(
            user_id=user_id,
            message=(f"Выбрана книга '{selected_book.title}'. Что нужно сделать?"),
            keyboard=self._create_book_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_selecting_action(self, context) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        state_info = context.get_state()

        if text.lower() == "удалить":
            book_service = BookService()
            book_id = state_info["data"]["selected_book_id"]
            if not book_id:
                api.messages.send(
                    user_id=user_id,
                    message="Ошибка: идентификатор книги отсутствует.",
                    keyboard=cancel_keyboard().get_keyboard(),
                    random_id=get_random_id(),
                )
                return

            deleted_book = book_service.delete_book(book_id)
            context.delete_state()
            api.messages.send(
                user_id=user_id,
                message=f"🗑️ Книга '{deleted_book.title}' удалена.",
                keyboard=main_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        if text.lower() == "прогресс":
            book_id = state_info["data"]["selected_book_id"]
            book_service = BookService()
            book = book_service.get_book_by_id(book_id)
            if not book:
                api.messages.send(
                    user_id=user_id,
                    message="⚠️ Книга не найдена.",
                    keyboard=cancel_keyboard().get_keyboard(),
                    random_id=get_random_id(),
                )
                return

            state_info["state"] = "waiting_for_progress_input"
            state_info["data"]["progress_book_pages"] = book.pages
            context.set_state(state_info)
            api.messages.send(
                user_id=user_id,
                message=(
                    f"📖 Выбрана книга '{book.title}'.\n"
                    f"Предыдущее значение - {book.current_page}. "
                    f"Введи текущую страницу (от 0 до {book.pages}):"
                ),
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        if text.lower() == "статус":
            book_id = state_info["data"]["selected_book_id"]
            book_service = BookService()
            book = book_service.get_book_by_id(book_id)
            if not book:
                api.messages.send(
                    user_id=user_id,
                    message="⚠️ Книга не найдена.",
                    keyboard=cancel_keyboard().get_keyboard(),
                    random_id=get_random_id(),
                )
                return

            state_info["state"] = "selecting_status"
            context.set_state(state_info)
            api.messages.send(
                user_id=user_id,
                message=(f"📖 Выбрана книга '{book.title}'. Выбери новый статус:"),
                keyboard=self._create_status_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        if text.lower() == "изменить":
            book_id = state_info["data"]["selected_book_id"]
            book_service = BookService()
            book = book_service.get_book_by_id(book_id)
            if not book:
                api.messages.send(
                    user_id=user_id,
                    message="⚠️ Книга не найдена.",
                    keyboard=cancel_keyboard().get_keyboard(),
                    random_id=get_random_id(),
                )
                return

            state_info["state"] = "editing_title"
            context.set_state(state_info)
            api.messages.send(
                user_id=user_id,
                message=(
                    f"Текущее название: '{book.title}'.\n"
                    "Введи новое или нажми 'Дальше' чтобы оставить."
                ),
                keyboard=self._create_edit_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

    def _handle_selecting_status_filter(self, context) -> None:
        api = context.api
        user_id = context.user_id
        payload = context.payload
        user = get_or_create_user(api, user_id)

        status = payload.get("status", "")
        book_service = BookService()
        books = book_service.filter_books(user.id, status=status)
        context.set_state(
            {
                "command": "/edit",
                "state": "selecting_book",
                "data": {"books": [book.id for book in books]},
            }
        )
        lines = ["📚 Введи номер книги для редактирования.\nБиблиотека:\n\n"]
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
        user = get_or_create_user(api, user_id)

        selected_tag = text.strip()
        book_service = BookService()
        books = book_service.filter_books(user.id, tags=[selected_tag])
        context.set_state(
            {
                "command": "/edit",
                "state": "selecting_book",
                "data": {"books": [book.id for book in books]},
            }
        )
        lines = ["📚 Введи номер книги для редактирования.\nБиблиотека:\n\n"]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        api.messages.send(
            user_id=user_id,
            message="".join(lines),
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_editing_title(self, context) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        state_info = context.get_state()

        if text.lower() == "дальше":
            new_title = None
        else:
            new_title = text.strip()

        state_info["data"]["new_title"] = new_title
        state_info["state"] = "editing_author"
        context.set_state(state_info)
        book_id = state_info["data"]["selected_book_id"]
        book = BookService().get_book_by_id(book_id)
        if not book:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        api.messages.send(
            user_id=user_id,
            message=(
                f"Текущий автор: '{book.author}'.\n"
                "Введи нового или нажми 'Дальше' чтобы оставить."
            ),
            keyboard=self._create_edit_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_editing_author(self, context) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        state_info = context.get_state()

        if text.lower() == "дальше":
            new_author = None
        else:
            new_author = text.strip()

        state_info["data"]["new_author"] = new_author
        state_info["state"] = "editing_pages"
        context.set_state(state_info)
        book_id = state_info["data"]["selected_book_id"]
        book = BookService().get_book_by_id(book_id)
        if not book:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        api.messages.send(
            user_id=user_id,
            message=(
                f"Текущее количество страниц: {book.pages}.\n"
                "Введи новое или нажми 'Дальше' чтобы оставить."
            ),
            keyboard=self._create_edit_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_editing_pages(self, context) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        state_info = context.get_state()

        if text.lower() == "дальше":
            new_pages = None
        else:
            try:
                new_pages = int(text.strip())
            except ValueError:
                api.messages.send(
                    user_id=user_id,
                    message="⚠️ Введи целое число для количества страниц.",
                    keyboard=self._create_edit_keyboard().get_keyboard(),
                    random_id=get_random_id(),
                )
                return

        state_info["data"]["new_pages"] = new_pages
        state_info["state"] = "editing_link"
        context.set_state(state_info)
        book_id = state_info["data"]["selected_book_id"]
        book = BookService().get_book_by_id(book_id)
        if not book:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        api.messages.send(
            user_id=user_id,
            message=(
                f"Текущая ссылка: {book.link or 'Отсутствует'}.\n"
                "Введи новую или нажми 'Дальше' чтобы оставить."
            ),
            keyboard=self._create_edit_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_editing_link(self, context) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        state_info = context.get_state()

        if text.lower() == "дальше":
            new_link = None
        else:
            new_link = text.strip()

        state_info["data"]["new_link"] = new_link
        state_info["state"] = "editing_tags"
        context.set_state(state_info)
        book_id = state_info["data"]["selected_book_id"]
        book = BookService().get_book_by_id(book_id)
        if not book:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        tags_text = ", ".join(book.tags) if book.tags else "Нет тэгов"
        api.messages.send(
            user_id=user_id,
            message=(
                f"Текущие тэги: {tags_text}.\n" "Введи новые через запятую или нажми 'Дальше'."
            ),
            keyboard=self._create_edit_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )

    def _handle_editing_tags(self, context) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        state_info = context.get_state()

        if text.lower() == "дальше":
            new_tags = None
        else:
            new_tags = [t.strip() for t in text.split(",") if t.strip()]

        book_id = state_info["data"]["selected_book_id"]
        book_service = BookService()
        book = book_service.get_book_by_id(book_id)
        if not book:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        if state_info["data"].get("new_title") is not None:
            book.title = state_info["data"]["new_title"]
        if state_info["data"].get("new_author") is not None:
            book.author = state_info["data"]["new_author"]
        if state_info["data"].get("new_pages") is not None:
            book.pages = state_info["data"]["new_pages"]
        if state_info["data"].get("new_link") is not None:
            book.link = state_info["data"]["new_link"]
        if new_tags is not None:
            book.tags = new_tags
        book_service.book_repo.update_book(book)
        api.messages.send(
            user_id=user_id,
            message=f"✅ Книга обновлена: '{book.title}' от {book.author}.",
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        context.delete_state()

    def _handle_selecting_status(self, context) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        state_info = context.get_state()

        status_map = {
            "хочу прочитать": "want_to_read",
            "читаю сейчас": "reading",
            "прочитано": "read",
            "отложено": "postponed",
        }
        new_status = status_map.get(text.lower())
        if not new_status:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Неизвестный статус. Выбери один из предложенных.",
                keyboard=self._create_status_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        book_id = state_info["data"]["selected_book_id"]
        book_service = BookService()
        updated_book = book_service.update_book_status(book_id, new_status)
        api.messages.send(
            user_id=user_id,
            message=(
                f"✅ Статус книги '{updated_book.title}' изменён на "
                f"'{get_status_name(updated_book.status.value)}'"
            ),
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        context.delete_state()

    def _handle_waiting_for_progress_input(self, context) -> None:
        api = context.api
        user_id = context.user_id
        text = context.text
        state_info = context.get_state()

        try:
            current_page = int(text.strip())
        except ValueError:
            api.messages.send(
                user_id=user_id,
                message="❌ Введи число (например: '50').",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        total_pages = state_info["data"].get("progress_book_pages")
        if total_pages is None:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Ошибка: неизвестное количество страниц книги.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        if current_page < 0:
            api.messages.send(
                user_id=user_id,
                message="❌ Страница не может быть отрицательной.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return
        if current_page > total_pages:
            api.messages.send(
                user_id=user_id,
                message=f"❌ Книга содержит только {total_pages} страниц.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        book_id = state_info["data"].get("selected_book_id")
        if not book_id:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Идентификатор книги не найден.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        book_service = BookService()
        updated_book = book_service.update_book_progress(book_id, current_page)
        api.messages.send(
            user_id=user_id,
            message=(
                f"✅ Прогресс чтения книги '{updated_book.title}' обновлён.\n"
                f"Прочитано {updated_book.current_page}"
                f" из {total_pages} страниц."
            ),
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        context.delete_state()

    @staticmethod
    def _create_book_keyboard() -> VkKeyboard:
        """Клавиатура действий над книгой."""
        kb = VkKeyboard()
        kb.add_button("Изменить")
        kb.add_button("Прогресс")
        kb.add_button("Статус")
        kb.add_line()
        kb.add_button("Удалить")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb

    @staticmethod
    def _create_status_keyboard() -> VkKeyboard:
        """Создаёт клавиатуру для выбора нового статуса книги без payload."""
        kb = VkKeyboard()
        kb.add_button("Хочу прочитать")
        kb.add_button("Читаю сейчас")
        kb.add_line()
        kb.add_button("Прочитано")
        kb.add_button("Отложено")
        kb.add_line()
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb

    @staticmethod
    def _create_edit_keyboard() -> VkKeyboard:
        """Keyboard with 'Дальше' and 'Отмена' for sequential editing."""
        kb = VkKeyboard()
        kb.add_button("Дальше")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb
