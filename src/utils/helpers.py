"""Вспомогательные функции для Book Shelf."""

import re
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
    status_emoji = get_status_emoji(book.status)

    tags_text = ", ".join(book.tags) if book.tags else "Нет тегов"

    progress_percent = _get_read_book_progress(book)
    return (
        f"{index}. {status_emoji} {book.title}\n"
        f"Теги: {tags_text}\n"
        f"Прогресс: {book.current_page}/{book.pages} ({progress_percent}%)\n"
    )


def format_book_details(book) -> str:
    """Форматирует информацию о книге для отображения."""
    status_emoji = get_status_emoji(book.status)
    progress_percent = _get_read_book_progress(book)
    return (
        f"{status_emoji} {book.title}\n"
        f"Автор: {book.author}\n"
        f"Тэги: {', '.join(book.tags) if book.tags else '—'}\n"
        f"Статус: {get_status_name(book.status.value)}\n"
        f"Прогресс: {book.current_page}/{book.pages} ({progress_percent}%)\n"
        f"Дата добавления: {book.created_at.strftime('%Y-%m-%d')}\n"
        f"Дата начала чтения: {book.reading_start_date.strftime('%Y-%m-%d') if book.reading_start_date else '—'}\n"
        f"Ссылка: {book.link or '—'}"
    )


def validate_book_data(title: str, author: str, pages: int) -> bool:
    """Валидирует данные книги."""
    if not title or not title.strip():
        return False

    if not author or not author.strip():
        return False

    if not isinstance(pages, int) or pages <= 0:
        return False

    return True

# TODO: Используй utils
def get_status_emoji(status: str) -> str:
    """Возвращает эмодзи для статуса книги."""
    emoji_map = {
        "want_to_read": "📎",
        "reading": "📖",
        "read": "📗",
        "postponed": "📘"
    }
    return emoji_map.get(status, "📙")

def get_status_name(status: str) -> str:
    """Возвращает название статуса книги на русском языке."""
    name_map = {
        "want_to_read": "Хочу прочитать",
        "reading": "Читаю",
        "read": "Прочитал",
        "postponed": "Отложил"
    }
    return name_map.get(status, "Неизвестный статус")

def sort_books_by_status(books: list) -> list:
    """Сортирует книги по статусам в порядке: читаю, хочу прочитать, отложено, прочитано.
    Если у объекта книги нет атрибута `status`, используется значение по умолчанию, чтобы не вызывать ошибку.
    """
    status_order = {
        "reading": 0,
        "want_to_read": 1,
        "postponed": 2,
        "read": 3
    }

    # Используем getattr для безопасного доступа к статусу; если его нет, ставим высокий порядок, сохраняющий исходный порядок
    return sorted(books, key=lambda book: status_order.get(getattr(book, "status", None), 999))

def is_valid_url(url: str) -> bool:
    """Return True if URL has http/https scheme and netloc."""
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


def _get_read_book_progress(book) -> int:
    return round((book.current_page / book.pages * 100)) if book.pages > 0 else 0