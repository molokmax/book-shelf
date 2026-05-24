import pytest
import uuid
from datetime import datetime, timedelta, date
from core.services import BookService, ReadingStatsService
from core.db import get_db
from core.models import User as ModelUser

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
        external_id=uuid.uuid4().int & 0x7fffffff,
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
        title="Avg Book",
        author="Author",
        tags=[],
        pages=300,
        user_id="1",
        link=None,
    )
    # Insert reading stats for last 30 days: 10 pages each day
    db = get_db(db_path)
    today = datetime.now().date()
    for days_ago in range(30):
        read_date = (today - timedelta(days=days_ago)).isoformat()
        db.add_reading_stat(book.id, pages_read=10, read_date=read_date)
    avg = reading_stats_service.avg_pages_per_day(book.id)
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
    # Update progress to 50
    book_service.update_book_progress(book.id, 50)
    # Insert stats: assume avg 10 pages per day over last 30 days
    db = get_db(db_path)
    today = datetime.now().date()
    for days_ago in range(30):
        read_date = (today - timedelta(days=days_ago)).isoformat()
        db.add_reading_stat(book.id, pages_read=10, read_date=read_date)
    pred = reading_stats_service.predict_completion_date(book.id)
    # Remaining pages = 150, avg 10 => 15 days needed
    expected = date.today() + timedelta(days=15)
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
    # No reading stats added → avg = 0
    pred = reading_stats_service.predict_completion_date(book.id)
    assert pred is None
