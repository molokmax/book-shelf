"""VK bot handler for adding books (manual method only)."""

from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id
from vk_api.vk_api import VkApiMethod

from core.services import BookService
from utils import helpers
from utils.litres_parser import (LitresParserError, is_litres_url,
                                 parse_litres_book)
from vk_bot.keyboards import cancel_keyboard, main_keyboard
from vk_bot.states import active_states
from vk_bot.user_helpers import get_or_create_user

# TODO: Разбить файл на функцию. Изучить как сделать через StateMachine


def handle_add_command(vk: VkApiMethod, user_id: int) -> None:
    """Entry point for the /add command. Starts method selection flow."""
    # Initialise state for this user
    active_states[user_id] = {"command": "/add", "state": "choose_method", "data": {}}
    vk.messages.send(
        user_id=user_id,
        message="➕ Добавление новой книги. Выбери способ добавления:",
        keyboard=create_add_method_keyboard().get_keyboard(),
        random_id=get_random_id(),
    )


def handle_add_command_step(vk: VkApiMethod, user_id: int, text: str) -> None:
    """Process a message from a user that is currently in the add flow."""
    if user_id not in active_states:
        # Not in add flow – ignore
        return

    state_info = active_states[user_id]
    state = state_info["state"]
    data = state_info["data"]

    text = text.strip()

    # New state: choose method
    if state == "choose_method":
        if text == "Ручное":
            state_info["state"] = "waiting_for_title"
            vk.messages.send(
                user_id=user_id,
                message="Отлично! Теперь введи название книги:",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
        elif text == "Из LitRes":
            state_info["state"] = "waiting_for_litres_url"
            vk.messages.send(
                user_id=user_id,
                message="Пожалуйста, введи ссылку на книгу с https://litres.ru:",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
        else:
            vk.messages.send(
                user_id=user_id,
                message="Пожалуйста, выбери один из вариантов: Ручное или Из https://litres.ru.",
                keyboard=create_add_method_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
        return

    if state == "waiting_for_title":
        data["title"] = text
        state_info["state"] = "waiting_for_author"
        vk.messages.send(
            user_id=user_id,
            message="Отлично! Теперь введи автора книги:",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    if state == "waiting_for_author":
        data["author"] = text
        state_info["state"] = "waiting_for_pages"
        vk.messages.send(
            user_id=user_id,
            message="Отлично! Теперь введи количество страниц в книге:",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    if state == "waiting_for_pages":
        try:
            pages = int(text)
            if pages <= 0:
                raise ValueError
        except ValueError:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Пожалуйста, введи корректное положительное целое число для количества страниц.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return
        data["pages"] = pages
        # Prompt for optional link first
        state_info["state"] = "waiting_for_link"
        vk.messages.send(
            user_id=user_id,
            message="Отлично! Теперь можешь указать ссылку на книгу. Нажми Дальше чтобы оставить пустым.",
            keyboard=create_link_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    if state == "waiting_for_link":
        if not text or text.lower() == "дальше":
            data["link"] = None
        else:
            link = text
            if not helpers.is_valid_url(link):
                vk.messages.send(
                    user_id=user_id,
                    message="⚠️ Пожалуйста, введи корректный URL (http/https) или нажми 'Дальше' to skip.",
                    keyboard=create_link_keyboard().get_keyboard(),
                    random_id=get_random_id(),
                )
                return
            data["link"] = link
        state_info["state"] = "waiting_for_tags"
        vk.messages.send(
            user_id=user_id,
            message="Хорошо! Теперь введи теги книги через запятую (например: Tech, Программирование):",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    if state == "waiting_for_tags":
        tags = [tag.strip() for tag in text.split(",") if tag.strip()]
        data["tags"] = tags
        # All data collected – create the book
        user = get_or_create_user(vk, user_id)
        book_service = BookService()
        book = book_service.create_book(
            title=data["title"],
            author=data["author"],
            tags=data["tags"],
            pages=data["pages"],
            user_id=user.id,
            link=data.get("link"),
        )
        # Clear state
        del active_states[user_id]
        message_text = (
            f"✅ Книга '{book.title}' успешно добавлена в твою библиотеку!\n"
            "\nТы можешь\n"
            "/add - Добавить ещё одну книгу\n"
            "/list - Показать список книг"
        )
        vk.messages.send(
            user_id=user_id,
            message=message_text,
            keyboard=create_book_added_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    # New state: waiting for LitRes URL
    if state == "waiting_for_litres_url":
        url = text.strip()
        if not is_litres_url(url):
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Пожалуйста, введи корректную ссылку на LitRes.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        try:
            book_data = parse_litres_book(url)
            # Validate essential fields
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
                    # optional cover/image could be stored if needed
                }
            )
            # Store LitRes URL as link
            data["link"] = url
            # Ask user to confirm the parsed book data before proceeding
            state_info["state"] = "waiting_for_litres_confirm"
            vk.messages.send(
                user_id=user_id,
                message=(
                    f"✅ Найдены данные книги:\n"
                    f"\nНазвание: {book_data.get('title', '—')}\n"
                    f"Автор: {book_data.get('author', '—')}\n"
                    f"Страниц: {book_data.get('pages', '—')}\n"
                    "\nПродолжить добавление?"
                ),
                keyboard=create_confirm_litres_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
        except LitresParserError as e:
            vk.messages.send(
                user_id=user_id,
                message=f"❌ Не удалось получить информацию о книге: {e}",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
        return

    if state == "waiting_for_litres_confirm":
        # User confirms parsed LitRes data before proceeding
        if text == "Продолжить":
            state_info["state"] = "waiting_for_litres_tags"
            vk.messages.send(
                user_id=user_id,
                message="Отлично! Теперь введи теги книги через запятую (например: Tech, Программирование):",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
        return

    if state == "waiting_for_litres_tags":
        tags = [tag.strip() for tag in text.split(",") if tag.strip()]
        data["tags"] = tags
        user = get_or_create_user(vk, user_id)
        book_service = BookService()
        book = book_service.create_book(
            title=data["title"],
            author=data["author"],
            tags=data["tags"],
            pages=data["pages"],
            user_id=user.id,
            link=data["link"],
        )
        del active_states[user_id]
        message_text = (
            f"✅ Книга '{book.title}' успешно добавлена в твою библиотеку!\n"
            "\nТы можешь\n"
            "/add - Добавить ещё одну книгу\n"
            "/list - Показать список книг"
        )
        vk.messages.send(
            user_id=user_id,
            message=message_text,
            keyboard=create_book_added_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    # Fallback – reset state if unknown
    del active_states[user_id]
    vk.messages.send(
        user_id=user_id,
        message="Состояние добавления книги сброшено. Пожалуйста, повтори команду /add.",
        keyboard=main_keyboard().get_keyboard(),
        random_id=get_random_id(),
    )


def create_book_added_keyboard() -> VkKeyboard:
    kb = VkKeyboard()
    kb.add_button("/add")
    kb.add_button("/list")
    return kb


def create_add_method_keyboard() -> VkKeyboard:
    """Keyboard for selecting add method (manual or LitRes)."""
    kb = VkKeyboard()
    kb.add_button("Ручное", payload={"command": "/add_manual"})
    kb.add_button("Из LitRes", payload={"command": "/add_litres"})
    kb.add_button("Отмена", payload={"command": "/cancel"})
    return kb


def create_link_keyboard() -> VkKeyboard:
    kb = VkKeyboard()
    kb.add_button("Дальше")
    kb.add_button("Отмена", payload={"command": "/cancel"})
    return kb


def create_confirm_litres_keyboard() -> VkKeyboard:
    """Keyboard for confirming parsed LitRes book data."""
    kb = VkKeyboard()
    kb.add_button("Продолжить")
    kb.add_button("Отмена", payload={"command": "/cancel"})
    return kb
