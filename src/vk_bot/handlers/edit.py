"""Обработчики команды /edit в VK‑боте (только удаление книги)."""

from vk_api.vk_api import VkApiMethod
from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id

from core.services import BookService
from utils import helpers
from utils import logger
from vk_bot.keyboards import main_keyboard, cancel_keyboard
from vk_bot.user_helpers import get_or_create_user
from vk_bot.states import active_states

log = logger.setup_logger(__name__)


def handle_edit_command(vk: VkApiMethod, user_id: int) -> None:
    """Инициирует процесс /edit – выводит нумерованный список книг и просит выбрать номер."""
    # 1. Получаем пользователя
    user = get_or_create_user(vk, user_id)

    # 2. Получаем и сортируем книги
    book_service = BookService()
    books = book_service.get_all_books(user.id)
    books = helpers.sort_books_by_status(books)

    # 3. Если книг нет – отправляем сообщение
    if not books:
        vk.messages.send(
            user_id=user_id,
            message="У тебя нет книг в библиотеке. Добавь книгу с помощью /add",
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        return

    # 4. Формируем нумерованный список в одном сообщении
    lines = ["📚 Введи номер книги, которую хочешь отредактировать.\nТвоя библиотека:\n\n"]
    for i, book in enumerate(books, 1):
        lines.append(helpers.format_book_info(i, book) + "\n")
    message_text = "".join(lines)

    # 5. Сохраняем состояние
    active_states[user_id] = {"command": "/edit", "state": "selecting_book", "data": {"books": [book.id for book in books]}}

    # 6. Отправляем список и запрос номера
    vk.messages.send(
        user_id=user_id,
        message=message_text,
        keyboard=cancel_keyboard().get_keyboard(),
        random_id=get_random_id()
    )


def handle_edit_command_step(vk: VkApiMethod, user_id: int, text: str) -> None:
    """Обрабатывает шаг после выбора книги в режиме /edit."""
    state_info = active_states.get(user_id)
    if not state_info or state_info.get("command") != "/edit":
        return
    
    state = state_info.get("state")

    if state == "selecting_book":
        # Ожидаем номер книги
        try:
            selection = int(text.strip())
        except ValueError:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Введи корректный номер книги.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        books_ids = state_info["data"]["books"]
        if selection < 1 or selection > len(books_ids):
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Номер книги вне диапазона.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        book_id = books_ids[selection - 1]
        book_service = BookService()
        selected_book = book_service.get_book_by_id(book_id)
        if not selected_book:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

        # Сохраняем выбранную книгу и переходим к выбору действия
        state_info["state"] = "selecting_action"
        state_info["data"]["selected_book_id"] = book_id
        # Предлагаем действие (пока только удаление)
        vk.messages.send(
            user_id=user_id,
            message=f"Выбрана книга '{selected_book.title}'. Что нужно сделать?",
            keyboard=create_book_keyboard(str(book_id)).get_keyboard(),
            random_id=get_random_id()
        )
        return
    
    if state == "selecting_action":
        if text.lower() == "удалить":
            book_service = BookService()
            book_id = state_info["data"]["selected_book_id"]
            if not book_id:
                vk.messages.send(
                    user_id=user_id,
                    message="Ошибка при удалении книги. Идентификатор выбранной книги отсутствует.",
                    keyboard=cancel_keyboard().get_keyboard(),
                    random_id=get_random_id()
                )
                return

            deleted_book = book_service.delete_book(book_id)
            del active_states[user_id]
            vk.messages.send(
                user_id=user_id,
                message=f"🗑️ Книга '{deleted_book.title}' удалена.",
                keyboard=main_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        
        elif text.lower() == "прогресс":
            # Начинаем процесс обновления прогресса чтения
            book_id = state_info["data"]["selected_book_id"]
            book_service = BookService()
            book = book_service.get_book_by_id(book_id)
            if not book:
                vk.messages.send(
                    user_id=user_id,
                    message="⚠️ Книга не найдена.",
                    keyboard=cancel_keyboard().get_keyboard(),
                    random_id=get_random_id()
                )
                return

            # Сохраняем состояние ожидания ввода текущей страницы
            state_info["state"] = "waiting_for_progress_input"
            state_info["data"]["progress_book_pages"] = book.pages
            vk.messages.send(
                user_id=user_id,
                message=(
                    f"📖 Выбрана книга '{book.title}'. Введи текущую страницу (от 0 до {book.pages}):"
                ),
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

    elif state == "waiting_for_progress_input":
        # Обработка ввода текущей страницы пользователем
        try:
            current_page = int(text.strip())
        except ValueError:
            vk.messages.send(
                user_id=user_id,
                message="❌ Некорректный ввод. Пожалуйста, введи число (например: '50').",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

        total_pages = state_info["data"].get("progress_book_pages")
        if total_pages is None:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Ошибка: неизвестное количество страниц книги.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

        if current_page < 0:
            vk.messages.send(
                user_id=user_id,
                message="❌ Страница не может быть отрицательной.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        if current_page > total_pages:
            vk.messages.send(
                user_id=user_id,
                message=f"❌ Книга содержит только {total_pages} страниц.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

        book_id = state_info["data"].get("selected_book_id")
        if not book_id:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Идентификатор книги не найден.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

        book_service = BookService()
        updated_book = book_service.update_book_progress(book_id, current_page)

        vk.messages.send(
            user_id=user_id,
            message=(
                f"✅ Прогресс чтения книги '{updated_book.title}' обновлён.\n"
                f"Прочитано {updated_book.current_page} из {total_pages} страниц."
            ),
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        # Очистить состояние
        del active_states[user_id]
        return


def create_book_keyboard(book_id: str) -> VkKeyboard:
    """Создаёт клавиатуру с кнопками действий над книгой: удалить и обновить прогресс."""
    kb = VkKeyboard()
    kb.add_button('Удалить')
    kb.add_button('Прогресс')
    kb.add_button('Отмена', payload={'command': '/cancel'})
    return kb
