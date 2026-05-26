"""Репозиторий для работы с данными."""

from datetime import date, datetime, timedelta
from typing import List, Optional

from core.database import Database
from core.models import Book, User
from utils import logger


class BookRepository:
    """Репозиторий для работы с книгами."""

    def __init__(self, db: Database | None = None, db_path: str = "data/database.db") -> None:
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
        if hasattr(self, "db") and self.db is not None:
            self.db.close()


class ReadStatsRepository:
    """Repository for reading statistics."""

    def __init__(self, db: Database | None = None, db_path: str = "data/database.db") -> None:
        """Initialize the repository."""
        self.db = db if db is not None else Database(db_path)
    
    
    def add_reading_stats(
        self, book_id: str, pages_read: int, read_date: str | None = None
    ) -> str:
        """Добавляет запись статистики чтения."""
        return self.db.add_reading_stat(book_id, pages_read, read_date)
    

    def fetch_reading_stats(self, book_id: str, from_date: date, to_date: date) -> int:
        """Return total pages read for a book between dates (inclusive)."""
        log = logger.setup_logger(__name__)
        log.debug(f"Fetching reading stats for book_id={book_id} from {from_date} to {to_date}")
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "SELECT SUM(pages_read) FROM read_stats WHERE book_id = ? AND read_date BETWEEN ? AND ?",
                (book_id, from_date.isoformat(), to_date.isoformat()),
            )
            result = cursor.fetchone()[0]
            return int(result) if result is not None else 0

    def fetch_average_pages_per_day(self, book_id: str, from_date: date) -> float:
        """Calculate average pages per day over the last *days* days."""
        log = logger.setup_logger(__name__)
        to_date = datetime.now().date()
        days = (to_date - from_date).days
        log.debug(f"Calculating average pages per day for book_id={book_id} over {days} days")
        total = self.fetch_reading_stats(book_id, from_date, to_date)
        return total / days if days > 0 else 0.0


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, db: Database | None = None, db_path: str = "data/database.db") -> None:
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
        if hasattr(self, "db") and self.db is not None:
            self.db.close()
