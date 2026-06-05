"""Обработчики команды /details в VK‑боте (просмотр подробной информации о книге)."""

from datetime import datetime, timedelta

from vk_api.utils import get_random_id

from core.services import BookService, ReadingStatsService
from utils import helpers, logger
from utils.helpers import format_book_details
from vk_bot.keyboards import (cancel_keyboard, filter_keyboard, main_keyboard,
                              status_keyboard, tags_keyboard)
from vk_bot.user_helpers import get_or_create_user

log = logger.setup_logger(__name__)


def handle_details(context) -> None:
    """Инициирует процесс /details – предлагает выбрать фильтр книг."""
    api = context.api
    user_id = context.user_id
    user = get_or_create_user(api, user_id)
    context.set_state(
        {
            "command": "/details",
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


def handle_details_step(context) -> None:
    """Обрабатывает ввод после команды /details и отправляет подробную информацию о выбранной книге."""
    api = context.api
    user_id = context.user_id
    text = context.text
    payload = context.payload
    state_info = context.get_state()
    if not state_info or state_info.get("command") != "/details":
        return

    user = get_or_create_user(api, user_id)

    # ---------- Выбор фильтра ----------
    if state_info.get("state") == "choose_filter":
        choice = text.strip().lower()
        if choice == "по статусу":
            state_info["state"] = "selecting_status_filter"
            api.messages.send(
                user_id=user_id,
                message="Выбери статус книги:",
                keyboard=status_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        elif choice == "по тегам":
            book_service = BookService()
            tags = book_service.get_all_tags(user.id)
            state_info["state"] = "selecting_tag_filter"
            api.messages.send(
                user_id=user_id,
                message="Выбери тег:",
                keyboard=tags_keyboard(tags).get_keyboard(),
                random_id=get_random_id(),
            )
            return

        elif choice == "все":
            # показать весь список книг
            book_service = BookService()
            books = book_service.get_all_books(user.id)
            books = helpers.sort_books_by_status(books)
            if not books:
                api.messages.send(
                    user_id=user_id,
                    message="У тебя нет книг в библиотеке. Добавь книгу с помощью /add",
                    keyboard=main_keyboard().get_keyboard(),
                    random_id=get_random_id(),
                )
                context.delete_state()
                return
            state_info["state"] = "selecting_book"
            state_info["data"]["books"] = [book.id for book in books]
            lines = [
                "📚 Введи номер книги, чтобы увидеть её детали.\nТвоя библиотека:\n\n"
            ]
            for i, book in enumerate(books, 1):
                lines.append(helpers.format_book_info(i, book) + "\n")
            api.messages.send(
                user_id=user_id,
                message="".join(lines),
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

        else:
            api.messages.send(
                user_id=user_id,
                message="⚠️ Выбери один из вариантов: По статусу, По тегам, Все",
                keyboard=filter_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            return

    # ---------- Выбор статуса ----------
    if state_info.get("state") == "selecting_status_filter":
        status = payload.get("status", "")
        # получить книги с этим статусом
        book_service = BookService()
        books = book_service.filter_books(user.id, status=status)
        books = helpers.sort_books_by_status(books)
        if not books:
            api.messages.send(
                user_id=user_id,
                message="Книг с выбранным статусом нет.",
                keyboard=main_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            context.delete_state()
            return
            state_info["state"] = "selecting_book"
            state_info["data"]["books"] = [book.id for book in books]
            lines = [
                "📚 Введи номер книги, чтобы увидеть её детали.\nКниги с выбранным статусом:\n\n"
            ]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        api.messages.send(
            user_id=user_id,
            message="".join(lines),
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    # ---------- Выбор тега ----------
    if state_info.get("state") == "selecting_tag_filter":
        selected_tag = text.strip()
        book_service = BookService()
        books = book_service.filter_books(user.id, tags=[selected_tag])
        books = helpers.sort_books_by_status(books)
        if not books:
            api.messages.send(
                user_id=user_id,
                message="Книг с выбранным тегом нет.",
                keyboard=main_keyboard().get_keyboard(),
                random_id=get_random_id(),
            )
            context.delete_state()
            return
        state_info["state"] = "selecting_book"
        state_info["data"]["books"] = [book.id for book in books]
        lines = [
            "📚 Введи номер книги, чтобы увидеть её детали.\nКниги с выбранным тегом:\n\n"
        ]
        for i, book in enumerate(books, 1):
            lines.append(helpers.format_book_info(i, book) + "\n")
        api.messages.send(
            user_id=user_id,
            message="".join(lines),
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    # ---------- Выбор книги ----------
    if state_info.get("state") != "selecting_book":
        return

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
    book = BookService().get_book_by_id(book_id)
    if not book:
        api.messages.send(
            user_id=user_id,
            message="⚠️ Книга не найдена.",
            keyboard=cancel_keyboard().get_keyboard(),
            random_id=get_random_id(),
        )
        return

    # Получаем статистику чтения
    stats_service = ReadingStatsService()
    today = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    week_start = (today - timedelta(days=7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    month_start = (today - timedelta(days=30)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    weekly_pages = stats_service.get_reading_stats(book.id, week_start, today)
    monthly_pages = stats_service.get_reading_stats(book.id, month_start, today)
    avg_pages = stats_service.avg_pages_per_day(book)
    pred_date = stats_service.predict_completion_date(book)
    details = format_book_details(
        book,
        weekly_pages=weekly_pages,
        monthly_pages=monthly_pages,
        avg_pages=avg_pages,
        predicted_date=pred_date,
    )
    api.messages.send(
        user_id=user_id,
        message=details,
        keyboard=main_keyboard().get_keyboard(),
        random_id=get_random_id(),
    )
    context.delete_state()
