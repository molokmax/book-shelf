"""Репозиторий для работы с данными."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from core.database import Database
from core.models import DAILY_PAGES_GOAL, Book, Goal, User
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
        self,
        book_id: str,
        pages_read: int,
        read_date: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """Добавляет запись статистики чтения."""
        return self.db.add_reading_stat(book_id, pages_read, read_date, user_id)

    def fetch_pages_by_user(self, user_id: str, from_date: datetime, to_date: datetime) -> int:
        """Сумма прочитанных страниц пользователя за период (включительно)."""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "SELECT SUM(pages_read) FROM read_stats "
                "WHERE user_id = ? AND read_date BETWEEN ? AND ?",
                (user_id, from_date.isoformat(), to_date.isoformat()),
            )
            result = cursor.fetchone()[0]
            return int(result) if result is not None else 0

    def fetch_reading_stats(self, book_id: str, from_date: datetime, to_date: datetime) -> int:
        """Return total pages read for a book between dates (inclusive)."""
        log = logger.setup_logger(__name__)
        log.debug(
            "Fetching reading stats for book_id=%s from %s to %s",
            book_id,
            from_date,
            to_date,
        )
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "SELECT SUM(pages_read) FROM read_stats "
                "WHERE book_id = ? AND read_date BETWEEN ? AND ?",
                (book_id, from_date.isoformat(), to_date.isoformat()),
            )
            result = cursor.fetchone()[0]
            return int(result) if result is not None else 0

    def fetch_average_pages_per_day(self, book_id: str, from_date: datetime) -> float:
        """Calculate average pages per day over the given period."""
        log = logger.setup_logger(__name__)
        to_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        days = (to_date + timedelta(microseconds=1) - from_date).days
        log.debug(
            "Calculating average pages per day for book_id=%s over %d days",
            book_id,
            days,
        )
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


class GoalRepository:
    """Репозиторий целей пользователя."""

    def __init__(self, db: Database | None = None, db_path: str = "data/database.db") -> None:
        self.db = db if db is not None else Database(db_path)

    def get_goal(self, user_id: str, kind: str = DAILY_PAGES_GOAL) -> Optional[Goal]:
        """Возвращает цель пользователя заданного вида."""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, kind, target, created_at, updated_at "
                "FROM goals WHERE user_id = ? AND kind = ?",
                (user_id, kind),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Goal(
                id=row[0],
                user_id=row[1],
                kind=row[2],
                target=row[3],
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5]),
            )

    def upsert_goal(self, user_id: str, target: int, kind: str = DAILY_PAGES_GOAL) -> Goal:
        """Создаёт или обновляет цель пользователя."""
        now = datetime.now()
        existing = self.get_goal(user_id, kind)
        with self.db.get_cursor() as cursor:
            if existing:
                cursor.execute(
                    "UPDATE goals SET target = ?, updated_at = ? " "WHERE user_id = ? AND kind = ?",
                    (target, now.isoformat(), user_id, kind),
                )
                return Goal(
                    id=existing.id,
                    user_id=user_id,
                    kind=kind,
                    target=target,
                    created_at=existing.created_at,
                    updated_at=now,
                )

            goal = Goal(user_id=user_id, kind=kind, target=target)
            cursor.execute(
                "INSERT INTO goals (id, user_id, kind, target, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    goal.id,
                    goal.user_id,
                    goal.kind,
                    goal.target,
                    goal.created_at.isoformat(),
                    goal.updated_at.isoformat(),
                ),
            )
            return goal

    def delete_goal(self, user_id: str, kind: str = DAILY_PAGES_GOAL) -> bool:
        """Удаляет цель пользователя. Возвращает True, если цель была."""
        with self.db.get_cursor() as cursor:
            cursor.execute("DELETE FROM goals WHERE user_id = ? AND kind = ?", (user_id, kind))
            return cursor.rowcount > 0


class UserStateRepository:
    """Хранилище состояния пользователя в таблице user_state."""

    def __init__(self, db: Database | None = None, db_path: str = "data/database.db") -> None:
        self.db = db if db is not None else Database(db_path)

    def get_state(self, user_id: str) -> Dict[str, Any]:
        """Возвращает состояние пользователя как словарь.

        Если запись отсутствует — возвращает пустой словарь.
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT json FROM user_state WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return {}
            return {}

    def save_state(self, user_id: str, state: Dict[str, Any]) -> None:
        """Сохраняет состояние пользователя."""
        json_state = json.dumps(state)
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "INSERT OR REPLACE INTO user_state " "(user_id, json) VALUES (?, ?)",
                (user_id, json_state),
            )

    def delete_state(self, user_id: str) -> None:
        """Удаляет запись состояния пользователя."""
        with self.db.get_cursor() as cursor:
            cursor.execute("DELETE FROM user_state WHERE user_id = ?", (user_id,))
