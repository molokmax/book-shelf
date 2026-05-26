"""Вспомогательные функции для Book Shelf."""

import re
from datetime import date
from urllib.parse import urlparse


def sanitize_text(text: str) -> str:
    """Очищает текст от нежелательных символов."""
    if not text:
        return ""

    # Удаляем лишние пробелы
    text = " ".join(text.split())

    # Удаляем специальные символы, которые могут вызвать проблемы
    text = re.sub(r"[^\w\sа-яА-ЯёЁ-]", "", text)

    return text.strip()


def format_book_info(index, book) -> str:
    """Форматирует информацию о книге для отображения."""
    status = getattr(book, "status", "unknown")
    status_emoji = get_status_emoji(status)

    tags = getattr(book, "tags", [])
    tags_text = ", ".join(tags) if tags else "Нет тегов"

    current_page = getattr(book, "current_page", 0)
    pages = getattr(book, "pages", 0)
    progress_percent = _get_read_book_progress(book)
    title = getattr(book, "title", "")
    return (
        f"{index}. {status_emoji} {title}\n"
        f"Теги: {tags_text}\n"
        f"Прогресс: {current_page}/{pages} ({progress_percent}%)\n"
    )


def format_book_details(book, weekly_pages: int | None = None, monthly_pages: int | None = None, avg_pages: float | None = None, predicted_date: date | None = None) -> str:
    """Форматирует информацию о книге для отображения, включая статистику чтения и прогноз."""
    status = getattr(book, "status", "unknown")
    status_emoji = get_status_emoji(status)
    progress_percent = _get_read_book_progress(book)
    lines = [
        f"{status_emoji} {book.title}",
        f"Автор: {book.author}",
        f"Ссылка: {book.link or '—'}",
        f"Тэги: {', '.join(book.tags) if book.tags else '—'}",
        f"Статус: {get_status_name(book.status.value)}",
        f"Прогресс: {book.current_page}/{book.pages} ({progress_percent}%)",
        f"Дата добавления: {book.created_at.strftime('%Y-%m-%d')}",
        f"Дата начала чтения: {book.reading_start_date.strftime('%Y-%m-%d') if book.reading_start_date else '—'}",
    ]
    if weekly_pages is not None:
        lines.append(f"За последнюю неделю прочитано: {weekly_pages} стр.")
    if monthly_pages is not None:
        lines.append(f"За последний месяц прочитано: {monthly_pages} стр.")
    if avg_pages is not None:
        if avg_pages == 0:
            lines.append("Недостаточно данных для оценки завершения")
        else:
            lines.append(f"Среднее за 30 дней: {avg_pages:.2f} стр/день")
    if predicted_date:
        lines.append(f"Ожидаемая дата завершения чтения: {predicted_date.strftime('%Y-%m-%d')}")
    return "\n".join(lines)


def validate_book_data(title: str, author: str, pages: int) -> bool:
    """Валидирует данные книги."""
    if not title or not title.strip():
        return False

    if not author or not author.strip():
        return False

    if not isinstance(pages, int) or pages <= 0:
        return False

    return True


def get_status_emoji(status: str) -> str:
    """Возвращает эмодзи для статуса книги."""
    emoji_map = {"want_to_read": "📎", "reading": "📖", "read": "📗", "postponed": "📘"}
    return emoji_map.get(status, "📙")


def get_status_name(status: str) -> str:
    """Возвращает название статуса книги на русском языке."""
    name_map = {
        "want_to_read": "Хочу прочитать",
        "reading": "Читаю",
        "read": "Прочитал",
        "postponed": "Отложил",
    }
    return name_map.get(status, "Неизвестный статус")


def sort_books_by_status(books: list) -> list:
    """Сортирует книги по статусам в порядке: читаю, хочу прочитать, отложено, прочитано.
    Если у объекта книги нет атрибута `status`, используется значение по умолчанию, чтобы не вызывать ошибку.
    """
    status_order = {"reading": 0, "want_to_read": 1, "postponed": 2, "read": 3}

    # Используем getattr для безопасного доступа к статусу; если его нет, ставим высокий порядок, сохраняющий исходный порядок
    return sorted(
        books, key=lambda book: status_order.get(getattr(book, "status", None), 999)
    )


def is_valid_url(url: str) -> bool:
    """Return True if URL has http/https scheme and netloc."""
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


def _get_read_book_progress(book) -> int:
    current_page = getattr(book, "current_page", 0)
    pages = getattr(book, "pages", 0)
    return round((current_page / pages * 100)) if pages > 0 else 0
