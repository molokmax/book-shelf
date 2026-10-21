import uuid
from datetime import date, datetime, timedelta

import pytest

from core.db import get_db
from core.models import User as ModelUser
from core.services import BookService, ReadingStatsService


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def services(db_path):
    # Initialize services with same DB path
    book_service = BookService(db_path=db_path)
    # Ensure a user exists (required by foreign key)
    user = ModelUser(
        id=str(uuid.uuid4()),
        external_id=uuid.uuid4().int & 0x7FFFFFFF,
        username="test",
        first_name="Test",
        last_name="User",
        created_at=datetime.now(),
        last_active=datetime.now(),
    )
    db = get_db(db_path)
    with db.get_cursor() as cur:
        cur.execute(
            "INSERT INTO users (id, external_id, username, first_name, last_name, created_at, last_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
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
    reading_stats_service = ReadingStatsService(db_path=db_path)
    return book_service, reading_stats_service, db_path


def test_average_pages_per_day(services):
    book_service, reading_stats_service, db_path = services
    # Create a book
    book = book_service.create_book(
        title="Avg Book", author="Author", tags=[], pages=300, user_id="1", link=None
    )
    book.reading_start_date = datetime.now() - timedelta(days=31)
    # Insert reading stats for last 30 days: 10 pages each day
    db = get_db(db_path)
    today = datetime.now()
    for days_ago in range(30):
        read_date = (today - timedelta(days=days_ago)).isoformat()
        db.add_reading_stat(book.id, pages_read=10, read_date=read_date)
    avg = reading_stats_service.avg_pages_per_day(book)
    assert avg == 10.0


def test_average_pages_per_day_just_started(services):
    book_service, reading_stats_service, db_path = services
    # Create a book
    book = book_service.create_book(
        title="Avg Book", author="Author", tags=[], pages=300, user_id="1", link=None
    )
    book.reading_start_date = datetime.now()
    # Insert reading stats for last 30 days: 10 pages each day
    db = get_db(db_path)
    read_date = datetime.now().isoformat()
    db.add_reading_stat(book.id, pages_read=10, read_date=read_date)
    avg = reading_stats_service.avg_pages_per_day(book)
    assert avg == 10.0


def test_predict_completion_date_with_data(services):
    book_service, reading_stats_service, db_path = services
    # Create a book with 200 pages, currently at 50 pages
    book = book_service.create_book(
        title="Predict Book",
        author="Author",
        tags=[],
        pages=200,
        user_id="1",
        link=None,
    )
    book.reading_start_date = datetime.now() - timedelta(days=31)
    book.current_page = 50
    # Insert stats: assume avg 10 pages per day over last 30 days
    db = get_db(db_path)
    today = datetime.now().date()
    for days_ago in range(30):
        read_date = (today - timedelta(days=days_ago)).isoformat()
        db.add_reading_stat(book.id, pages_read=10, read_date=read_date)
    pred = reading_stats_service.predict_completion_date(book)
    # Remaining pages = 150, avg 10 => 15 days needed
    expected = date.today() + timedelta(days=1) + timedelta(days=15)
    assert pred == expected


def test_predict_completion_date_no_data(services):
    book_service, reading_stats_service, _ = services
    book = book_service.create_book(
        title="NoData Book",
        author="Author",
        tags=[],
        pages=100,
        user_id="1",
        link=None,
    )
    book.reading_start_date = datetime.now() - timedelta(days=31)
    # No reading stats added → avg = 0
    pred = reading_stats_service.predict_completion_date(book)
    assert pred is None


def test_predict_days_to_completion_with_data(services):
    book_service, reading_stats_service, db_path = services
    # Книга на 200 страниц, прочитано 50
    book = book_service.create_book(
        title="Days Book",
        author="Author",
        tags=[],
        pages=200,
        user_id="1",
        link=None,
    )
    book.reading_start_date = datetime.now() - timedelta(days=31)
    book.current_page = 50
    # Статистика: 10 страниц в день за последние 30 дней.
    # Полные datetime-строки, чтобы все 30 записей попали в окно: средняя ровно 10
    db = get_db(db_path)
    now = datetime.now()
    for days_ago in range(30):
        read_date = (now - timedelta(days=days_ago)).isoformat()
        db.add_reading_stat(book.id, pages_read=10, read_date=read_date)
    # Остаток 150 / средняя 10 = 15 дней
    assert reading_stats_service.predict_days_to_completion(book) == 15


def test_predict_days_to_completion_rounds_up(services):
    book_service, reading_stats_service, db_path = services
    book = book_service.create_book(
        title="Round Days Book",
        author="Author",
        tags=[],
        pages=200,
        user_id="1",
        link=None,
    )
    book.reading_start_date = datetime.now() - timedelta(days=31)
    book.current_page = 49  # остаток 151
    db = get_db(db_path)
    now = datetime.now()
    for days_ago in range(30):
        read_date = (now - timedelta(days=days_ago)).isoformat()
        db.add_reading_stat(book.id, pages_read=10, read_date=read_date)
    # 151 / 10 = 15.1 → округление вверх → 16
    assert reading_stats_service.predict_days_to_completion(book) == 16


def test_predict_days_to_completion_no_data(services):
    book_service, reading_stats_service, _ = services
    book = book_service.create_book(
        title="NoDays Book",
        author="Author",
        tags=[],
        pages=100,
        user_id="1",
        link=None,
    )
    book.reading_start_date = datetime.now() - timedelta(days=31)
    # Нет записей статистики → средняя 0 → прогноз невозможен
    assert reading_stats_service.predict_days_to_completion(book) is None


def test_predict_days_to_completion_finished_book(services):
    book_service, reading_stats_service, _ = services
    book = book_service.create_book(
        title="Done Days Book",
        author="Author",
        tags=[],
        pages=100,
        user_id="1",
        link=None,
    )
    book.current_page = 100
    # Книга дочитана: 0 дней, дата завершения = сегодня
    assert reading_stats_service.predict_days_to_completion(book) == 0
    assert reading_stats_service.predict_completion_date(book) == date.today()
