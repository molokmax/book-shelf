"""Вспомогательные функции для Book Shelf."""

import re
from telegram import Update
from core.models import User
from core.services import UserService

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

    tags_text = ", ".join(book.tags) if book.tags else "Нет тегов"

    return (
        f"{status_emoji} {priority_emoji} **{book.title}**\n"
        f"*Автор:* {book.author}\n"
        f"*Теги:* {tags_text}\n"
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

def get_or_create_user(update: Update) -> User:
    """Получает или создаёт пользователя в системе."""
    user_service = UserService()
    return user_service.get_or_create_user(
        update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name
    )
