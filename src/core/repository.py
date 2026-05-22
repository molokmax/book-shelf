"""Репозиторий для работы с данными."""

from typing import List, Optional

from core.database import Database
from core.models import Book, User


class BookRepository:
    """Репозиторий для работы с книгами."""

    def __init__(self, db: Database = None, db_path: str = "data/database.db") -> None:
        """Инициализация репозитория."""
        self.db = db if db is not None else Database(db_path)

    def get_all_books(self) -> List[Book]:
        """Получает все книги."""
        return self.db.get_all_books()

    def get_book_by_id(self, book_id: str) -> Optional[Book]:
        """Получает книгу по ID."""
        return self.db.get_book_by_id(book_id)

    def add_book(self, book: Book) -> Book:
        """Добавляет новую книгу."""
        return self.db.add_or_update_book(book)

    def update_book(self, book: Book) -> Book:
        """Обновляет книгу."""
        return self.db.add_or_update_book(book)

    def delete_book(self, book_id: str) -> Book:
        """Удаляет книгу по ID."""
        book = self.db.delete_book(book_id)
        if not book:
            raise ValueError(f"Книга с ID {book_id} не найдена")
        return book

    def get_books_by_status(self, status: str) -> List[Book]:
        """Получает книги по статусу."""
        return self.db.get_books_by_status(status)

    def get_books_by_user_id(self, user_id: str) -> List[Book]:
        """Получает книги по ID пользователя."""
        return self.db.get_books_by_user_id(user_id)

    def close(self) -> None:
        """Закрывает подключение к базе данных."""
        if hasattr(self, 'db') and self.db is not None:
            self.db.close()

class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, db: Database = None, db_path: str = "data/database.db") -> None:
        """Инициализация репозитория."""
        self.db = db if db is not None else Database(db_path)

    def get_user_by_external_id(self, external_id: int) -> Optional[User]:
        """Получает пользователя по Telegram ID."""
        return self.db.get_user_by_external_id(external_id)

    def add_user(self, user: User) -> User:
        """Добавляет нового пользователя."""
        return self.db.add_or_update_user(user)

    def update_user(self, user: User) -> User:
        """Обновляет пользователя."""
        return self.db.add_or_update_user(user)

    def get_all_users(self) -> List[User]:
        """Получает всех пользователей."""
        return self.db.get_all_users()

    def close(self) -> None:
        """Закрывает подключение к базе данных."""
        if hasattr(self, 'db') and self.db is not None:
            self.db.close()
