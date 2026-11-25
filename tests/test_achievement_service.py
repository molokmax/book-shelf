"""Тесты каталога и сервиса достижений."""

from datetime import datetime

import pytest

from core.db import close_db, get_db
from core.models import ACHIEVEMENT_DEFINITIONS, AchievementMetric, ReadingStatus
from core.services import AchievementService, BookService, ReadingStatsService

NOW = datetime(2026, 11, 24, 12, 30)


@pytest.fixture
def env(tmp_path):
    close_db()
    db_path = str(tmp_path / "achievement-service.db")
    achievement_service = AchievementService(db_path=db_path)
    book_service = BookService(db_path=db_path)
    stats_service = ReadingStatsService(db_path=db_path)
    db = get_db(db_path)
    with db.get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (id, external_id, created_at, last_active) VALUES (?, ?, ?, ?)",
            ("user-1", 1, NOW.isoformat(), NOW.isoformat()),
        )
    yield achievement_service, book_service, stats_service, db
    close_db()


def add_books(book_service, count, read_count=0, user_id="user-1"):
    books = []
    for index in range(count):
        status = ReadingStatus.READ.value if index < read_count else ReadingStatus.READING.value
        books.append(
            book_service.create_book(
                title=f"Book {index}",
                author="Author",
                tags=[],
                pages=200,
                user_id=user_id,
                status=status,
            )
        )
    return books


def statuses_by_key(result):
    return {status.definition.key: status for status in result.statuses}


def test_achievement_catalog_has_stable_order_and_rules():
    assert [item.key for item in ACHIEVEMENT_DEFINITIONS] == [
        "books_1",
        "books_10",
        "read_books_1",
        "read_books_5",
        "pages_100",
        "pages_1000",
    ]
    assert [item.title for item in ACHIEVEMENT_DEFINITIONS] == [
        "Первая книга",
        "Своя библиотека",
        "Первый финиш",
        "Читатель",
        "Сотня страниц",
        "Тысяча страниц",
    ]
    assert [item.target for item in ACHIEVEMENT_DEFINITIONS] == [1, 10, 1, 5, 100, 1000]
    assert [item.metric for item in ACHIEVEMENT_DEFINITIONS] == [
        AchievementMetric.BOOKS,
        AchievementMetric.BOOKS,
        AchievementMetric.READ_BOOKS,
        AchievementMetric.READ_BOOKS,
        AchievementMetric.PAGES,
        AchievementMetric.PAGES,
    ]
    assert all(item.description for item in ACHIEVEMENT_DEFINITIONS)


def test_check_without_data_returns_zero_progress(env):
    service, _, _, _ = env

    result = service.check("user-1", NOW)

    assert result.new_achievements == []
    assert len(result.statuses) == 6
    assert all(status.current == 0 for status in result.statuses)
    assert all(not status.is_unlocked for status in result.statuses)


def test_check_unlocks_first_book_only_once(env):
    service, book_service, _, db = env
    add_books(book_service, 1)

    first = service.check("user-1", NOW)
    second = service.check("user-1", NOW)

    assert [item.key for item in first.new_achievements] == ["books_1"]
    assert second.new_achievements == []
    assert statuses_by_key(second)["books_1"].unlocked_at == NOW
    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM user_achievements WHERE user_id = 'user-1'")
        assert cursor.fetchone()[0] == 1


def test_check_retrospectively_unlocks_all_thresholds_in_catalog_order(env):
    service, book_service, stats_service, _ = env
    books = add_books(book_service, 10, read_count=5)
    stats_service.add_record(books[0].id, 1000, user_id="user-1")

    result = service.check("user-1", NOW)

    assert [item.key for item in result.new_achievements] == [
        item.key for item in ACHIEVEMENT_DEFINITIONS
    ]
    assert all(status.is_unlocked for status in result.statuses)
    assert all(status.unlocked_at == NOW for status in result.statuses)


def test_check_reports_partial_progress_and_keeps_unlocked_achievements(env):
    service, book_service, stats_service, _ = env
    books = add_books(book_service, 4, read_count=1)
    stats_service.add_record(books[0].id, 105, user_id="user-1")

    first = service.check("user-1", NOW)
    statuses = statuses_by_key(first)

    assert [item.key for item in first.new_achievements] == [
        "books_1",
        "read_books_1",
        "pages_100",
    ]
    assert statuses["books_10"].current == 4
    assert statuses["read_books_5"].current == 1
    assert statuses["pages_1000"].current == 105

    book_service.delete_book(books[-1].id)
    book_service.update_book_status(books[0].id, ReadingStatus.READING.value)
    second = service.check("user-1", NOW)
    updated = statuses_by_key(second)

    assert updated["books_10"].current == 3
    assert not updated["books_10"].is_unlocked
    assert updated["read_books_5"].current == 0
    assert updated["books_1"].is_unlocked
    assert updated["read_books_1"].is_unlocked
    assert updated["pages_100"].is_unlocked


def test_check_pages_use_positive_deltas_after_rollback(env):
    service, book_service, _, _ = env
    book = add_books(book_service, 1)[0]

    book_service.update_book_progress(book.id, 80)
    first = service.check("user-1", NOW)
    assert statuses_by_key(first)["pages_100"].current == 80
    assert not statuses_by_key(first)["pages_100"].is_unlocked

    book_service.update_book_progress(book.id, 20)
    book_service.update_book_progress(book.id, 50)
    second = service.check("user-1", NOW)

    assert statuses_by_key(second)["pages_100"].current == 110
    assert statuses_by_key(second)["pages_100"].is_unlocked


def test_manual_read_status_does_not_add_pages(env):
    service, book_service, _, _ = env
    book = add_books(book_service, 1)[0]

    book_service.update_book_status(book.id, ReadingStatus.READ.value)
    result = service.check("user-1", NOW)
    statuses = statuses_by_key(result)

    assert statuses["read_books_1"].is_unlocked
    assert statuses["pages_100"].current == 0
    assert not statuses["pages_100"].is_unlocked


def test_check_does_not_unlock_achievements_for_another_user(env):
    service, book_service, _, db = env
    add_books(book_service, 1)
    service.check("user-1", NOW)
    with db.get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (id, external_id, created_at, last_active) VALUES (?, ?, ?, ?)",
            ("user-2", 2, NOW.isoformat(), NOW.isoformat()),
        )

    result = service.check("user-2", NOW)

    assert result.new_achievements == []
    assert all(status.current == 0 for status in result.statuses)
    assert all(not status.is_unlocked for status in result.statuses)
