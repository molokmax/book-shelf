"""Tests for link handling in BookService."""

import pytest
from core.services import BookService, UserService
from core.models import ReadingStatus, User


@pytest.fixture
def service(tmp_path):
    # Use a temporary SQLite DB
    db_file = tmp_path / "test.db"
    svc = BookService(db_path=str(db_file))
    # Ensure a user exists (required by foreign key)
    user_svc = UserService(db_path=str(db_file))
    user_svc.get_or_create_user(
        user_external_id=1, user_factory=lambda uid: User(id=str(uid), external_id=uid)
    )
    return svc


def test_create_book_with_valid_link(service):
    book = service.create_book(
        title="Test Book",
        author="Author",
        tags=[],
        pages=100,
        user_id="1",
        link="https://example.com/book",
    )
    assert book.link == "https://example.com/book"
    assert book.title == "Test Book"
    assert book.status == ReadingStatus.WANT_TO_READ


def test_create_book_without_link(service):
    book = service.create_book(
        title="No Link", author="Author", tags=[], pages=50, user_id="1", link=None
    )
    assert book.link is None


def test_edit_book_link(service):
    # Create initial book
    book = service.create_book(
        title="Edit Link",
        author="Author",
        tags=[],
        pages=30,
        user_id="1",
        link="https://old.com",
    )
    # Update link via repository directly for simplicity
    repo = service.book_repo
    book.link = "https://new.com"
    updated = repo.update_book(book)
    assert updated.link == "https://new.com"
