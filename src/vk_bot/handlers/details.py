"""Обработчики команды /details в VK‑боте (просмотр подробной информации о книге)."""

from datetime import datetime, timedelta

from vk_api.utils import get_random_id
from vk_api.vk_api import VkApiMethod

from core.services import BookService, ReadingStatsService
from utils import helpers, logger
from utils.helpers import (format_book_details, get_status_emoji,
                           get_status_name)
from vk_bot.keyboards import cancel_keyboard, main_keyboard
from vk_bot.states import active_states
from vk_bot.user_helpers import get_or_create_user

log = logger.setup_logger(__name__)


def handle_details(vk: VkApiMethod, user_id: int) -> None:
    """Инициирует процесс /details – выводит нумерованный список книг и ждёт номер от пользователя."""
    user = get_or_create_user(vk, user_id)
    book_service = BookService()
    books = book_service.get_all_books(user.id)
    books = helpers.sort_books_by_status(books)

    if not books:
        vk.messages.send(
            user_id=user_id,
            message="У тебя нет книг в библиотеке. Добавь книгу с помощью /add",
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    lines = ["📚 Введи номер книги, чтобы увидеть её детали.\nТвоя библиотека:\n\n"]
    for i, book in enumerate(books, 1):
        lines.append(helpers.format_book_info(i, book) + "\n")
    message_text = "".join(lines)

    # сохраняем состояние
    active_states[user_id] = {
        "command": "/details",
        "state": "selecting_book",
        "data": {"books": [book.id for book in books]},
    }

    vk.messages.send(
        user_id=user_id,
        message=message_text,
        keyboard=cancel_keyboard().get_keyboard(),
        random_id=get_random_id(),
    )


def handle_details_step(vk: VkApiMethod, user_id: int, text: str) -> None:
    """Обрабатывает ввод номера книги после команды /details и отправляет подробную информацию."""
    state_info = active_states.get(user_id)
    if not state_info or state_info.get("command") != "/details":
        return

    if state_info.get("state") != "selecting_book":
        return

    try:
        selection = int(text.strip())
    except ValueError:
        vk.messages.send(
            user_id=user_id,
            message="⚠️ Введи корректный номер книги.",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    books_ids = state_info["data"]["books"]
    if selection < 1 or selection > len(books_ids):
        vk.messages.send(
            user_id=user_id,
            message="⚠️ Номер книги вне диапазона.",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    book_id = books_ids[selection - 1]
    book = BookService().get_book_by_id(book_id)
    if not book:
        vk.messages.send(
            user_id=user_id,
            message="⚠️ Книга не найдена.",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    # Получаем статистику чтения
    stats_service = ReadingStatsService()
    today = datetime.now().date()
    week_start = today - timedelta(days=7)
    month_start = today - timedelta(days=30)
    weekly_pages = stats_service.get_reading_stats(book.id, week_start, today)
    monthly_pages = stats_service.get_reading_stats(book.id, month_start, today)
    avg_pages = stats_service.avg_pages_per_day(book)
    pred_date = stats_service.predict_completion_date(book)
    # Формируем детали книги с добавленными данными
    details = format_book_details(
        book,
        weekly_pages=weekly_pages,
        monthly_pages=monthly_pages,
        avg_pages=avg_pages,
        predicted_date=pred_date,
    )
    vk.messages.send(
        user_id=user_id,
        message=details,
        keyboard=main_keyboard().get_keyboard(),
        random_id=get_random_id(),
    )
    # Очистить состояние
    del active_states[user_id]
