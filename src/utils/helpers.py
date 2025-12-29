"""Вспомогательные функции для Book Shelf."""

from typing import Optional
import re

def sanitize_text(text: str) -> str:
    """Очищает текст от нежелательных символов."""
    if not text:
        return ""

    # Удаляем лишние пробелы
    text = " ".join(text.split())

    # Удаляем специальные символы, которые могут вызвать проблемы
    text = re.sub(r"[^\w\sа-яА-ЯёЁ-]", "", text)

    return text.strip()

def format_book_info(book) -> str:
    """Форматирует информацию о книге для отображения."""
    status_emoji = {
        "want_to_read": "📖",
        "reading": "📚",
        "read": "📕",
        "postponed": "⏸️"
    }.get(book.status, "📘")

    priority_emoji = {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢"
    }.get(book.priority, "⚪")

    return (
        f"{status_emoji} {priority_emoji} **{book.title}**\n"
        f"*Автор:* {book.author}\n"
        f"*Жанр:* {book.genre}\n"
        f"*Страниц:* {book.pages}\n"
        f"*Прогресс:* {book.progress}%\n"
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
