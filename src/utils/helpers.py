"""Вспомогательные функции для Book Shelf."""

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

def format_book_info(index, book) -> str:
    """Форматирует информацию о книге для отображения."""
    status_emoji = get_status_emoji(book.status)

    tags_text = ", ".join(book.tags) if book.tags else "Нет тегов"

    progress_percent = round((book.current_page / book.pages * 100)) if book.pages > 0 else 0
    return (
        f"{index}. {status_emoji} **{book.title}**\n"
        f"*Автор:* {book.author}\n"
        f"*Теги:* {tags_text}\n"
        f"*Страниц:* {book.pages}\n"
        f"*Прогресс:* {book.current_page}/{book.pages} ({progress_percent}%)\n"
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

def get_status_emoji(status: str) -> str:
    """Возвращает эмодзи для статуса книги."""
    emoji_map = {
        "want_to_read": "📖",
        "reading": "📚",
        "read": "📕",
        "postponed": "⏸️"
    }
    return emoji_map.get(status, "📘")

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
    """Сортирует книги по статусам в порядке: читаю, хочу прочитать, отложено, прочитано."""
    status_order = {
        "reading": 0,
        "want_to_read": 1,
        "postponed": 2,
        "read": 3
    }

    return sorted(books, key=lambda book: status_order.get(book.status, 999))
