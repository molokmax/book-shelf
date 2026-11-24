"""Тесты сервиса дневной цели чтения (уровень БД)."""

import uuid
from datetime import date, datetime, timedelta

import pytest

from core.db import get_db
from core.models import User
from core.services import BookService, GoalService, ReadingStatsService

STREAK_NOW = datetime(2026, 1, 10, 12, 0)


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


def prepare_streak(env, target=50, created_day=date(2026, 1, 1)):
    book_service, goal_service, stats_service, db, user_id = env
    book = create_book(book_service, user_id)
    goal_service.set_daily_goal(user_id, target)
    with db.get_cursor() as cur:
        cur.execute(
            "UPDATE goals SET created_at = ? WHERE user_id = ?",
            (datetime.combine(created_day, datetime.min.time()).isoformat(), user_id),
        )
    return goal_service, stats_service, db, book.id, user_id


def add_pages(stats_service, book_id, user_id, day, pages, hour=12):
    stats_service.add_record(
        book_id,
        pages,
        read_date=datetime(day.year, day.month, day.day, hour).isoformat(),
        user_id=user_id,
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


def test_fetch_daily_pages_by_user_aggregates_and_filters(env):
    book_service, goal_service, stats_service, db, user_id = env
    first = create_book(book_service, user_id, "First")
    second = create_book(book_service, user_id, "Second")
    other_user_id = make_other_user(db)

    stats_service.add_record(first.id, 20, read_date="2026-01-01", user_id=user_id)
    stats_service.add_record(second.id, 15, read_date="2026-01-01T12:00:00", user_id=user_id)
    stats_service.add_record(first.id, 5, read_date="2026-01-02T23:59:59", user_id=user_id)
    stats_service.add_record(first.id, 100, read_date="2026-01-01T10:00:00", user_id=other_user_id)
    db.add_reading_stat(first.id, 50, read_date="2026-01-01T11:00:00")
    stats_service.add_record(first.id, 10, read_date="2025-12-31T23:59:59", user_id=user_id)
    stats_service.add_record(first.id, 10, read_date="2026-01-03T00:00:00", user_id=user_id)

    daily_pages = goal_service.read_stats_repo.fetch_daily_pages_by_user(
        user_id, date(2026, 1, 1), date(2026, 1, 3)
    )

    assert daily_pages == {date(2026, 1, 1): 35, date(2026, 1, 2): 5}


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


@pytest.mark.parametrize(
    ("pages", "expected"),
    [([20, 15, 14], 0), ([20, 15, 15], 1), ([60], 1)],
)
def test_current_streak_aggregates_pages_and_requires_target(env, pages, expected):
    goal_service, stats_service, _, book_id, user_id = prepare_streak(env)
    for pages_read in pages:
        add_pages(stats_service, book_id, user_id, STREAK_NOW.date(), pages_read)

    assert goal_service.get_current_streak(user_id, STREAK_NOW) == expected


def test_current_streak_counts_through_completed_today(env):
    goal_service, stats_service, _, book_id, user_id = prepare_streak(env)
    for day in (date(2026, 1, 8), date(2026, 1, 9), date(2026, 1, 10)):
        add_pages(stats_service, book_id, user_id, day, 50)

    assert goal_service.get_current_streak(user_id, STREAK_NOW) == 3


def test_current_streak_preserves_yesterday_when_today_incomplete(env):
    goal_service, stats_service, _, book_id, user_id = prepare_streak(env)
    add_pages(stats_service, book_id, user_id, date(2026, 1, 8), 50)
    add_pages(stats_service, book_id, user_id, date(2026, 1, 9), 50)
    add_pages(stats_service, book_id, user_id, date(2026, 1, 10), 10)

    assert goal_service.get_current_streak(user_id, STREAK_NOW) == 2


def test_current_streak_returns_zero_after_missed_yesterday(env):
    goal_service, stats_service, _, book_id, user_id = prepare_streak(env)
    add_pages(stats_service, book_id, user_id, date(2026, 1, 8), 50)
    add_pages(stats_service, book_id, user_id, date(2026, 1, 10), 10)

    assert goal_service.get_current_streak(user_id, STREAK_NOW) == 0


def test_current_streak_starts_new_series_after_gap(env):
    goal_service, stats_service, _, book_id, user_id = prepare_streak(env)
    add_pages(stats_service, book_id, user_id, date(2026, 1, 8), 50)
    add_pages(stats_service, book_id, user_id, date(2026, 1, 10), 50)

    assert goal_service.get_current_streak(user_id, STREAK_NOW) == 1


def test_current_streak_ignores_days_before_goal_creation(env):
    goal_service, stats_service, _, book_id, user_id = prepare_streak(
        env, created_day=date(2026, 1, 9)
    )
    add_pages(stats_service, book_id, user_id, date(2026, 1, 7), 50)
    add_pages(stats_service, book_id, user_id, date(2026, 1, 8), 50)

    assert goal_service.get_current_streak(user_id, STREAK_NOW) == 0


def test_current_streak_includes_entire_creation_day(env):
    goal_service, stats_service, db, book_id, user_id = prepare_streak(
        env, created_day=STREAK_NOW.date()
    )
    with db.get_cursor() as cur:
        cur.execute(
            "UPDATE goals SET created_at = ? WHERE user_id = ?",
            ("2026-01-10T18:00:00", user_id),
        )
    add_pages(stats_service, book_id, user_id, STREAK_NOW.date(), 50, hour=8)

    assert goal_service.get_current_streak(user_id, STREAK_NOW) == 1


def test_current_streak_recalculates_when_target_changes(env):
    goal_service, stats_service, _, book_id, user_id = prepare_streak(env, target=30)
    add_pages(stats_service, book_id, user_id, date(2026, 1, 9), 40)
    add_pages(stats_service, book_id, user_id, date(2026, 1, 10), 40)
    assert goal_service.get_current_streak(user_id, STREAK_NOW) == 2

    goal_service.set_daily_goal(user_id, 50)
    assert goal_service.get_current_streak(user_id, STREAK_NOW) == 0

    goal_service.set_daily_goal(user_id, 40)
    assert goal_service.get_current_streak(user_id, STREAK_NOW) == 2


def test_current_streak_resets_after_disable_and_recreate(env):
    goal_service, stats_service, db, book_id, user_id = prepare_streak(env)
    add_pages(stats_service, book_id, user_id, date(2026, 1, 9), 50)

    goal_service.disable_goal(user_id)
    assert goal_service.get_current_streak(user_id, STREAK_NOW) is None

    goal_service.set_daily_goal(user_id, 50)
    with db.get_cursor() as cur:
        cur.execute(
            "UPDATE goals SET created_at = ? WHERE user_id = ?",
            ("2026-01-10T09:00:00", user_id),
        )
    assert goal_service.get_current_streak(user_id, STREAK_NOW) == 0

    add_pages(stats_service, book_id, user_id, date(2026, 1, 10), 50)
    assert goal_service.get_current_streak(user_id, STREAK_NOW) == 1


def test_goal_status_uses_now_and_single_history_query(env, monkeypatch):
    goal_service, stats_service, _, book_id, user_id = prepare_streak(
        env, created_day=date(2026, 1, 9)
    )
    add_pages(stats_service, book_id, user_id, date(2026, 1, 9), 50)
    calls = {"goal": 0, "daily": 0}
    original_get_goal = goal_service.goal_repo.get_goal
    original_fetch_daily = goal_service.read_stats_repo.fetch_daily_pages_by_user

    def tracked_get_goal(*args, **kwargs):
        calls["goal"] += 1
        return original_get_goal(*args, **kwargs)

    def tracked_fetch_daily(*args, **kwargs):
        calls["daily"] += 1
        return original_fetch_daily(*args, **kwargs)

    monkeypatch.setattr(goal_service.goal_repo, "get_goal", tracked_get_goal)
    monkeypatch.setattr(
        goal_service.read_stats_repo, "fetch_daily_pages_by_user", tracked_fetch_daily
    )

    status = goal_service.get_goal_status(user_id, now=STREAK_NOW)

    assert status.pages_today == 0
    assert status.percent == 0
    assert status.completed is False
    assert status.remaining == 50
    assert status.streak == 1
    assert calls == {"goal": 1, "daily": 1}
