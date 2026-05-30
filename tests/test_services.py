import pytest
from core.services import BookService
from core.models import ReadingStatus
from unittest.mock import patch


# Use a fake repository via monkeypatching BookService's internal repository
class FakeRepo:
    def __init__(self, books):
        self._books = books

    def get_all_books(self):
        return self._books

    def get_books_by_user_id(self, user_id):
        return self._books


books = [
    # status reading, tags ['fantasy']
    type(
        "B", (), {"status": ReadingStatus.READING, "tags": ["fantasy", "adventure"]}
    )(),
    # status want_to_read, tags ['sci-fi']
    type("B", (), {"status": ReadingStatus.WANT_TO_READ, "tags": ["sci-fi"]})(),
    # status read, tags []
    type("B", (), {"status": ReadingStatus.READ, "tags": []})(),
]


def test_filter_by_status():
    service = BookService()
    service.book_repo = FakeRepo(books)
    result = service.filter_books(user_id="42", status="reading")
    assert len(result) == 1
    assert result[0].status == ReadingStatus.READING


def test_filter_by_tag():
    service = BookService()
    service.book_repo = FakeRepo(books)
    result = service.filter_books(user_id="42", tags=["sci-fi"])
    assert len(result) == 1
    assert "sci-fi" in result[0].tags


def test_filter_by_status_and_tag():
    service = BookService()
    service.book_repo = FakeRepo(books)
    result = service.filter_books(user_id="42", status="reading", tags=["fantasy"])
    assert len(result) == 1
    assert result[0].status == ReadingStatus.READING
    assert "fantasy" in result[0].tags
