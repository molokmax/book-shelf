"""Тесты сервиса дневной цели чтения (уровень БД)."""

import uuid
from datetime import datetime, timedelta

import pytest

from core.db import get_db
from core.models import User
from core.services import BookService, GoalService, ReadingStatsService


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def env(db_path):
    book_service = BookService(db_path=db_path)
    goal_service = GoalService(db_path=db_path)
    stats_service = ReadingStatsService(db_path=db_path)

    user_id = str(uuid.uuid4())
    user = User(id=user_id, external_id=uuid.uuid4().int & 0x7FFFFFFF)
    db = get_db(db_path)
    with db.get_cursor() as cur:
        cur.execute(
            "INSERT INTO users "
            "(id, external_id, username, first_name, last_name, created_at, last_active) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user.id,
                user.external_id,
                user.username,
                user.first_name,
                user.last_name,
                user.created_at.isoformat(),
                user.last_active.isoformat(),
            ),
        )
    return book_service, goal_service, stats_service, db, user_id


def create_book(book_service, user_id, title="Book", pages=200):
    return book_service.create_book(
        title=title, author="Author", tags=[], pages=pages, user_id=user_id, link=None
    )


def make_other_user(db):
    user_id = str(uuid.uuid4())
    external_id = uuid.uuid4().int & 0x7FFFFFFF
    with db.get_cursor() as cur:
        cur.execute(
            "INSERT INTO users "
            "(id, external_id, username, first_name, last_name, created_at, last_active) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                external_id,
                None,
                None,
                None,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )
    return user_id


def test_set_goal_creates_and_updates_single_row(env):
    _, goal_service, _, db, user_id = env

    goal = goal_service.set_daily_goal(user_id, 50)
    assert goal.target == 50

    updated = goal_service.set_daily_goal(user_id, 30)
    assert updated.target == 30

    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*), MAX(target) FROM goals WHERE user_id = ?", (user_id,))
        count, target = cur.fetchone()
    assert count == 1
    assert target == 30


def test_disable_goal(env):
    _, goal_service, _, _, user_id = env

    goal_service.set_daily_goal(user_id, 50)
    assert goal_service.disable_goal(user_id) is True
    assert goal_service.get_goal(user_id) is None
    assert goal_service.disable_goal(user_id) is False


def test_today_pages_sums_all_user_books(env):
    book_service, goal_service, _, db, user_id = env

    first = create_book(book_service, user_id, "First")
    second = create_book(book_service, user_id, "Second")
    book_service.update_book_progress(first.id, 20)
    book_service.update_book_progress(second.id, 15)

    other_user_id = make_other_user(db)
    other_book = create_book(book_service, other_user_id, "Other")
    book_service.update_book_progress(other_book.id, 100)

    assert goal_service.today_pages(user_id) == 35


def test_today_pages_ignores_yesterday(env):
    book_service, goal_service, stats_service, _, user_id = env

    book = create_book(book_service, user_id)
    yesterday = datetime.now() - timedelta(days=1)
    stats_service.add_record(book.id, 10, read_date=yesterday.isoformat(), user_id=user_id)
    stats_service.add_record(book.id, 5, user_id=user_id)

    assert goal_service.today_pages(user_id) == 5


def test_today_pages_ignores_null_user_id(env):
    book_service, goal_service, _, db, user_id = env

    book = create_book(book_service, user_id)
    db.add_reading_stat(book.id, pages_read=30)
    db.add_reading_stat(book.id, pages_read=5, user_id=user_id)

    assert goal_service.today_pages(user_id) == 5


def test_goal_status_progress_and_completion(env):
    book_service, goal_service, _, _, user_id = env

    goal_service.set_daily_goal(user_id, 50)
    book = create_book(book_service, user_id)
    book_service.update_book_progress(book.id, 35)

    status = goal_service.get_goal_status(user_id)
    assert status.goal.target == 50
    assert status.pages_today == 35
    assert status.percent == 70
    assert status.completed is False
    assert status.remaining == 15

    book_service.update_book_progress(book.id, 60)
    status = goal_service.get_goal_status(user_id)
    assert status.pages_today == 60
    assert status.percent == 100
    assert status.completed is True
    assert status.remaining == 0


def test_goal_status_without_goal(env):
    _, goal_service, _, _, user_id = env

    assert goal_service.get_goal_status(user_id) is None
