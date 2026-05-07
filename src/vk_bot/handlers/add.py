'''VK bot handler for adding books (manual method only).'''

from vk_api.vk_api import VkApiMethod
from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id

from core.services import BookService
from vk_bot.user_helpers import get_or_create_user
from vk_bot.states import active_states
from vk_bot.keyboards import cancel_keyboard, start_keyboard

# TODO: Везде добавить клавиатуру cancel + добавить обработку команды cancel

def handle_add_command(vk: VkApiMethod, user_id: int) -> None:
    """Entry point for the /add command. Starts a manual add flow."""
    # Initialise state for this user
    active_states[user_id] = {"command": "/add", "state": "waiting_for_title", "data": {}}
    vk.messages.send(
        user_id=user_id,
        message="➕ Добавление новой книги\n\nПожалуйста, введи название книги:",
        keyboard=cancel_keyboard().get_keyboard(),
        random_id=get_random_id()
    )

def handle_add_command_step(user_id: int, vk: VkApiMethod, text: str) -> None:
    """Process a message from a user that is currently in the add flow."""
    if user_id not in active_states:
        # Not in add flow – ignore
        return

    state_info = active_states[user_id]
    state = state_info["state"]
    data = state_info["data"]

    if state == "waiting_for_title":
        data["title"] = text.strip()
        state_info["state"] = "waiting_for_author"
        vk.messages.send(
            user_id=user_id,
            message="Отлично! Теперь введи автора книги:",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        return

    if state == "waiting_for_author":
        data["author"] = text.strip()
        state_info["state"] = "waiting_for_pages"
        vk.messages.send(
            user_id=user_id,
            message="Отлично! Теперь введи количество страниц в книге:",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        return

    if state == "waiting_for_pages":
        try:
            pages = int(text.strip())
            if pages <= 0:
                raise ValueError
        except ValueError:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Пожалуйста, введи корректное положительное целое число для количества страниц.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        data["pages"] = pages
        state_info["state"] = "waiting_for_tags"
        vk.messages.send(
            user_id=user_id,
            message="Хорошо! Теперь введи теги книги через запятую (например: Tech, Программирование):",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id()
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
            user_id=user.id
        )
        # Clear state
        del active_states[user_id]
        vk.messages.send(
            user_id=user_id,
            message=f"✅ Книга '{book.title}' успешно добавлена в твою библиотеку!\n\nТы можешь\n/list - Показать список книг\n/add - Добавить ещё одну книгу",
            keyboard=create_book_added_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        return

    # Fallback – reset state if unknown
    del active_states[user_id]
    vk.messages.send(
        user_id=user_id,
        message="Состояние добавления книги сброшено. Пожалуйста, повтори команду /add.",
        keyboard=start_keyboard().get_keyboard(),
        random_id=get_random_id()
    )

def create_book_added_keyboard() -> VkKeyboard:
    kb = VkKeyboard()
    kb.add_button('/list')
    kb.add_button('/add')
    return kb