import uuid
from datetime import date, datetime, time, timedelta

from core.db import get_db
from core.models import ReadingStatus, User
from core.repository import UserSettingsRepository
from core.services import BookService, ReadingSummaryService


def _create_user(db) -> str:
    user = User(id=str(uuid.uuid4()), external_id=uuid.uuid4().int & 0x7FFFFFFF)
    db.add_or_update_user(user)
    return user.id


def _add_book(
    service: BookService,
    user_id: str,
    title: str,
    pages: int,
    status: ReadingStatus = ReadingStatus.WANT_TO_READ,
    current_page: int = 0,
    reading_start_date: datetime | None = None,
    reading_end_date: datetime | None = None,
):
    book = service.create_book(
        title=title,
        author="Author",
        tags=[],
        pages=pages,
        current_page=current_page,
        status=status.value,
        user_id=user_id,
    )
    book.reading_start_date = reading_start_date
    book.reading_end_date = reading_end_date
    return service.book_repo.update_book(book)


def _add_stat(db, book_id: str, user_id: str, day: date, pages: int) -> None:
    db.add_reading_stat(
        book_id,
        pages_read=pages,
        read_date=datetime.combine(day, time(12)).isoformat(),
        user_id=user_id,
    )


def test_book_service_returns_existing_overall_stats(tmp_path):
    db_path = str(tmp_path / "stats.db")
    db = get_db(db_path)
    user_id = _create_user(db)
    service = BookService(db_path)
    _add_book(service, user_id, "Read", 100, ReadingStatus.READ, 100)
    _add_book(service, user_id, "Reading", 100, ReadingStatus.READING, 40)
    _add_book(service, user_id, "Want", 100, ReadingStatus.WANT_TO_READ, 20)
    _add_book(service, user_id, "Postponed", 100, ReadingStatus.POSTPONED, 10)

    stats = service.get_stats(user_id)

    assert stats == {
        "total_books": 4,
        "read_books": 1,
        "reading_books": 1,
        "want_to_read_books": 1,
        "postponed_books": 1,
        "total_pages": 400,
        "read_pages": 170,
        "avg_progress": 42.5,
    }


def test_periods_include_current_and_analogous_previous_ranges(tmp_path):
    db_path = str(tmp_path / "periods.db")
    db = get_db(db_path)
    user_id = _create_user(db)
    books = BookService(db_path)
    stat_book = _add_book(books, user_id, "Stats", 1000)
    today = date(2026, 11, 25)
    _add_stat(db, stat_book.id, user_id, date(2026, 11, 24), 30)
    _add_stat(db, stat_book.id, user_id, date(2026, 11, 17), 10)
    _add_stat(db, stat_book.id, user_id, date(2026, 11, 19), 100)
    _add_stat(db, stat_book.id, user_id, date(2026, 11, 1), 20)
    _add_stat(db, stat_book.id, user_id, date(2026, 10, 25), 5)
    _add_stat(db, stat_book.id, user_id, date(2025, 11, 25), 7)
    _add_stat(db, stat_book.id, user_id, date(2025, 11, 26), 100)
    _add_book(
        books,
        user_id,
        "Read this year",
        100,
        ReadingStatus.READ,
        reading_end_date=datetime(2026, 11, 25),
    )
    _add_book(
        books,
        user_id,
        "Read at year start",
        100,
        ReadingStatus.READ,
        reading_end_date=datetime(2026, 1, 1),
    )
    _add_book(
        books,
        user_id,
        "Read previous year",
        100,
        ReadingStatus.READ,
        reading_end_date=datetime(2025, 10, 10),
    )
    _add_book(
        books,
        user_id,
        "Outside previous range",
        100,
        ReadingStatus.READ,
        reading_end_date=datetime(2025, 11, 26),
    )
    _add_book(books, user_id, "Read without date", 100, ReadingStatus.READ)

    summary = ReadingSummaryService(db_path).get_summary(user_id, today)

    assert (summary.week.pages.current, summary.week.pages.previous) == (30, 10)
    assert (summary.month.pages.current, summary.month.pages.previous) == (160, 5)
    assert (summary.year.pages.current, summary.year.pages.previous) == (165, 7)
    assert summary.year.read_books is not None
    assert (summary.year.read_books.current, summary.year.read_books.previous) == (2, 1)
    assert summary.week.read_books is None
    assert summary.month.read_books is None


def test_previous_month_is_clamped_to_its_last_day(tmp_path):
    db_path = str(tmp_path / "short-month.db")
    db = get_db(db_path)
    user_id = _create_user(db)
    books = BookService(db_path)
    book = _add_book(books, user_id, "Stats", 100)
    _add_stat(db, book.id, user_id, date(2026, 2, 1), 2)
    _add_stat(db, book.id, user_id, date(2026, 2, 28), 5)
    _add_stat(db, book.id, user_id, date(2026, 3, 31), 10)

    summary = ReadingSummaryService(db_path).get_summary(user_id, date(2026, 3, 31))

    assert summary.month.pages.previous == 7


def test_previous_year_uses_matching_date_and_clamps_leap_day(tmp_path):
    db_path = str(tmp_path / "leap-year.db")
    db = get_db(db_path)
    user_id = _create_user(db)
    books = BookService(db_path)
    book = _add_book(books, user_id, "Stats", 100)
    _add_stat(db, book.id, user_id, date(2026, 2, 28), 7)
    _add_stat(db, book.id, user_id, date(2026, 3, 1), 8)
    _add_stat(db, book.id, user_id, date(2027, 2, 28), 4)
    _add_stat(db, book.id, user_id, date(2027, 3, 1), 16)
    service = ReadingSummaryService(db_path)

    non_leap_summary = service.get_summary(user_id, date(2027, 3, 1))
    leap_summary = service.get_summary(user_id, date(2028, 2, 29))

    assert non_leap_summary.year.pages.previous == 15
    assert leap_summary.year.pages.previous == 4


def test_forecasts_use_own_then_overall_speed_and_queue_uses_full_pages(tmp_path):
    db_path = str(tmp_path / "forecasts.db")
    db = get_db(db_path)
    user_id = _create_user(db)
    books = BookService(db_path)
    today = date(2026, 11, 25)
    start = datetime(2026, 10, 1)
    own_speed_book = _add_book(
        books,
        user_id,
        "Own speed",
        150,
        ReadingStatus.READING,
        current_page=100,
        reading_start_date=start,
    )
    fallback_book = _add_book(
        books,
        user_id,
        "Fallback speed",
        120,
        ReadingStatus.READING,
        current_page=20,
        reading_start_date=start,
    )
    _add_book(books, user_id, "Want 1", 100)
    _add_book(books, user_id, "Want 2", 51, current_page=20)
    for offset in range(30):
        _add_stat(db, own_speed_book.id, user_id, today - timedelta(days=offset), 10)

    summary = ReadingSummaryService(db_path).get_summary(user_id, today)

    assert [forecast.book.title for forecast in summary.reading_forecasts] == [
        "Own speed",
        "Fallback speed",
    ]
    assert summary.reading_forecasts[0].completion_date == date(2026, 11, 30)
    assert summary.reading_forecasts[1].completion_date == date(2026, 12, 5)
    assert summary.want_to_read_count == 2
    assert summary.want_to_read_completion_date == date(2026, 12, 21)


def test_queue_without_current_books_starts_today_and_uses_configured_speed(tmp_path):
    db_path = str(tmp_path / "queue.db")
    db = get_db(db_path)
    user_id = _create_user(db)
    UserSettingsRepository(db).set_reading_speed_period(user_id, 7)
    books = BookService(db_path)
    today = date(2026, 11, 25)
    history_book = _add_book(books, user_id, "History", 300, ReadingStatus.READ, 300)
    _add_book(books, user_id, "Want", 100)
    for offset in range(30):
        pages = 20 if offset < 7 else 10
        _add_stat(db, history_book.id, user_id, today - timedelta(days=offset), pages)

    summary = ReadingSummaryService(db_path).get_summary(user_id, today)

    assert summary.reading_forecasts == []
    assert summary.want_to_read_completion_date == date(2026, 11, 30)


def test_zero_speed_makes_forecasts_unavailable(tmp_path):
    db_path = str(tmp_path / "no-speed.db")
    db = get_db(db_path)
    user_id = _create_user(db)
    books = BookService(db_path)
    _add_book(
        books,
        user_id,
        "Reading",
        100,
        ReadingStatus.READING,
        reading_start_date=datetime(2026, 10, 1),
    )
    _add_book(books, user_id, "Want", 100)

    summary = ReadingSummaryService(db_path).get_summary(user_id, date(2026, 11, 25))

    assert summary.reading_forecasts[0].completion_date is None
    assert summary.want_to_read_completion_date is None
