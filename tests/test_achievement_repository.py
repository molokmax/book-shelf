"""Тесты репозиториев метрик и полученных достижений."""

from datetime import datetime

import pytest

from core.database import Database
from core.models import Book, ReadingStatus
from core.repository import AchievementRepository, BookRepository, ReadStatsRepository

NOW = datetime(2026, 11, 24, 12, 30)


@pytest.fixture
def db(tmp_path):
    database = Database(str(tmp_path / "achievements.db"))
    yield database
    database.close()


def add_user(db: Database, user_id: str, external_id: int) -> None:
    with db.get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (id, external_id, created_at, last_active) VALUES (?, ?, ?, ?)",
            (user_id, external_id, NOW.isoformat(), NOW.isoformat()),
        )


def add_book(
    db: Database,
    user_id: str,
    title: str,
    status: ReadingStatus = ReadingStatus.WANT_TO_READ,
) -> Book:
    return BookRepository(db).add_book(
        Book(title=title, author="Author", pages=200, user_id=user_id, status=status)
    )


def test_unlock_is_idempotent_and_scoped_to_user(db):
    add_user(db, "user-1", 1)
    add_user(db, "user-2", 2)
    repository = AchievementRepository(db)

    assert repository.unlock("user-1", ["books_1", "pages_100"], NOW) == [
        "books_1",
        "pages_100",
    ]
    assert repository.unlock("user-1", ["books_1", "pages_100"], NOW) == []
    assert repository.unlock("user-2", ["books_1"], NOW) == ["books_1"]
    assert repository.unlock("user-1", [], NOW) == []

    unlocked = repository.get_unlocked("user-1")
    assert unlocked == {"books_1": NOW, "pages_100": NOW}
    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM user_achievements")
        assert cursor.fetchone()[0] == 3


def test_book_metrics_count_current_books_and_read_statuses(db):
    add_user(db, "user-1", 1)
    add_user(db, "user-2", 2)
    repository = BookRepository(db)

    assert repository.count_books_by_user("user-1") == (0, 0)

    add_book(db, "user-1", "Read", ReadingStatus.READ)
    add_book(db, "user-1", "Reading", ReadingStatus.READING)
    add_book(db, "user-1", "Postponed", ReadingStatus.POSTPONED)
    add_book(db, "user-1", "Planned")
    add_book(db, "user-2", "Other", ReadingStatus.READ)

    assert repository.count_books_by_user("user-1") == (4, 1)
    assert repository.count_books_by_user("user-2") == (1, 1)


def test_page_metrics_sum_all_history_without_ownerless_rows_or_book_join(db):
    add_user(db, "user-1", 1)
    add_user(db, "user-2", 2)
    first = add_book(db, "user-1", "First")
    second = add_book(db, "user-1", "Second")
    other = add_book(db, "user-2", "Other")
    repository = ReadStatsRepository(db)

    assert repository.fetch_total_pages_by_user("user-1") == 0

    repository.add_reading_stats(first.id, 40, user_id="user-1")
    repository.add_reading_stats(second.id, 35, user_id="user-1")
    repository.add_reading_stats(first.id, 30, user_id="user-1")
    repository.add_reading_stats(first.id, 50)
    repository.add_reading_stats(other.id, 100, user_id="user-2")

    assert repository.fetch_total_pages_by_user("user-1") == 105

    db.conn.execute("PRAGMA foreign_keys = OFF")
    db.conn.execute("DELETE FROM books WHERE id = ?", (first.id,))
    db.conn.commit()
    db.conn.execute("PRAGMA foreign_keys = ON")

    assert repository.fetch_total_pages_by_user("user-1") == 105
    assert BookRepository(db).count_books_by_user("user-1") == (1, 0)
