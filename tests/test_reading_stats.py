import pytest

from core.db import get_db
from core.models import User
from core.services import BookService, ReadingStatsService, UserService


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def services(db_path):
    # Initialize services with same DB path
    book_service = BookService(db_path=db_path)
    user_service = UserService(db_path=db_path)
    # Ensure a user exists (required by foreign key)
    user_service.get_or_create_user(
        user_external_id=1, user_factory=lambda uid: User(id=str(uid), external_id=uid)
    )
    reading_stats_service = ReadingStatsService(db_path=db_path)
    return book_service, reading_stats_service


def test_reading_stats_record_creation(services):
    book_service, reading_stats_service = services
    # Create a book
    book = book_service.create_book(
        title="Stat Book",
        author="Author",
        tags=[],
        pages=200,
        user_id="1",
        link=None,
    )
    # Update progress to page 30
    book_service.update_book_progress(book.id, 30)
    # Verify a reading stat record exists with pages_read = 30
    db = get_db(book_service.book_repo.db.db_path)  # reuse same DB path
    with db.get_cursor() as cur:
        cur.execute("SELECT pages_read FROM read_stats WHERE book_id = ?", (book.id,))
        rows = cur.fetchall()
    assert rows, "No reading stats record found"
    # Should have a single record with pages_read equal to 30
    assert len(rows) == 1
    assert rows[0][0] == 30
