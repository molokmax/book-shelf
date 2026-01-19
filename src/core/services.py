"""Сервисный слой для работы с книгами."""

from utils import logger
from typing import List, Dict, Optional
from datetime import datetime

from core.models import Book, User, ReadingStatus
from core.repository import BookRepository, UserRepository

log = logger.setup_logger(__name__)

class BookService:
    """Сервис для работы с книгами."""

    def __init__(self) -> None:
        """Инициализация сервиса."""
        self.book_repo = BookRepository()
        self.user_repo = UserRepository()

    def create_book(
        self,
        title: str,
        author: str,
        tags: list[str],
        pages: int,
        user_id: str,
        current_page: int = 0,
        status: str = ReadingStatus.WANT_TO_READ.value
    ) -> Book:
        """Создаёт новую книгу."""
        book = Book(
            title=title,
            author=author,
            tags=tags,
            pages=pages,
            user_id=user_id,
            current_page=current_page,
            status=ReadingStatus(status)
        )
        return self.book_repo.add_book(book)

    def get_all_books(self, user_id: Optional[str] = None) -> List[Book]:
        """Получает все книги. Если указан user_id, возвращает только книги этого пользователя.
        По умолчанию сортирует по приоритету (от высокого к низкому).
        Прочитанные книги всегда в конце списка."""
        books = self.book_repo.get_all_books() if user_id is None else self.book_repo.get_books_by_user_id(user_id)

        # Прочитанные книги всегда в конце
        books.sort(key=lambda b: b.status == ReadingStatus.READ)

        return books

    def get_book_by_id(self, book_id: str) -> Optional[Book]:
        """Получает книгу по ID."""
        return self.book_repo.get_book_by_id(book_id)

    def update_book_status(self, book_id: str, status: str) -> Book:
        """Обновляет статус книги."""
        book = self.book_repo.get_book_by_id(book_id)
        if not book:
            raise ValueError(f"Книга с ID {book_id} не найдена")

        book.status = ReadingStatus(status)
        book.updated_at = datetime.now()

        # Если статус "Читаю сейчас" и текущая страница 0, устанавливаем дату начала
        if status == ReadingStatus.READING.value and book.current_page == 0:
            book.reading_start_date = datetime.now()

        # Если статус "Прочитано" и текущая страница равна общему количеству страниц, устанавливаем дату окончания
        if status == ReadingStatus.READ.value and book.current_page == book.pages:
            book.reading_end_date = datetime.now()

        return self.book_repo.update_book(book)

    def update_book_progress(self, book_id: str, current_page: int) -> Book:
        """Обновляет прогресс чтения книги по текущей странице."""
        book = self.book_repo.get_book_by_id(book_id)
        if not book:
            raise ValueError(f"Книга с ID {book_id} не найдена")

        book.update_progress(current_page)

        # Автоматически обновляем статус
        if current_page == book.pages:
            book.status = ReadingStatus.READ
            book.reading_end_date = datetime.now()
        elif current_page > 0 and book.status == ReadingStatus.WANT_TO_READ:
            book.status = ReadingStatus.READING
            if not book.reading_start_date:
                book.reading_start_date = datetime.now()

        return self.book_repo.update_book(book)

    def delete_book(self, book_id: str) -> Book:
        """Удаляет книгу."""
        return self.book_repo.delete_book(book_id)

    def get_stats(self, user_id: Optional[str] = None) -> Dict:
        """Получает статистику чтения. Если указан user_id, возвращает статистику только для книг этого пользователя."""
        books = self.get_all_books(user_id)

        total_books = len(books)
        read_books = len([b for b in books if b.status == ReadingStatus.READ])
        reading_books = len([b for b in books if b.status == ReadingStatus.READING])
        want_to_read_books = len([b for b in books if b.status == ReadingStatus.WANT_TO_READ])
        postponed_books = len([b for b in books if b.status == ReadingStatus.POSTPONED])

        total_pages = sum(b.pages for b in books)
        read_pages = sum(b.current_page for b in books)
        avg_progress = (sum(b.current_page for b in books) / sum(b.pages for b in books) * 100) if books and sum(b.pages for b in books) > 0 else 0

        return {
            "total_books": total_books,
            "read_books": read_books,
            "reading_books": reading_books,
            "want_to_read_books": want_to_read_books,
            "postponed_books": postponed_books,
            "total_pages": total_pages,
            "read_pages": int(read_pages),
            "avg_progress": avg_progress
        }

    def export_library(self, user_id: Optional[str] = None) -> Dict:
        """Экспортирует библиотеку в формат для сохранения. Если указан user_id, экспортирует только книги этого пользователя."""
        books = self.get_all_books(user_id)
        return {
            "exported_at": datetime.now().isoformat(),
            "total_books": len(books),
            "books": [book.to_dict() for book in books]
        }

class UserService:
    """Сервис для работы с пользователями."""

    def __init__(self) -> None:
        """Инициализация сервиса."""
        self.user_repo = UserRepository()

    def get_or_create_user(self, telegram_id: int, **kwargs) -> User:
        """Получает пользователя или создаёт нового."""
        user = self.user_repo.get_user_by_telegram_id(telegram_id)

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=kwargs.get("username"),
                first_name=kwargs.get("first_name"),
                last_name=kwargs.get("last_name")
            )
            user = self.user_repo.add_user(user)

        # Обновляем последнюю активность
        user.last_active = datetime.now()
        return self.user_repo.update_user(user)
