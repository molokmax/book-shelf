"""Extended tests for link handling in BookService and add_litres command."""

import pytest
from core.services import BookService, UserService
from core.models import ReadingStatus, User


@pytest.fixture
def service(tmp_path):
    db_file = tmp_path / "test.db"
    svc = BookService(db_path=str(db_file))
    user_svc = UserService(db_path=str(db_file))
    user_svc.get_or_create_user(
        user_external_id=1,
        user_factory=lambda uid: User(id=str(uid), external_id=uid),
    )
    return svc


def test_create_book_with_valid_link(service):
    book = service.create_book(
        title="Link Book",
        author="Author",
        tags=[],
        pages=120,
        user_id="1",
        link="https://example.com",
    )
    assert book.link == "https://example.com"


def test_create_book_without_link(service):
    book = service.create_book(
        title="No Link",
        author="Author",
        tags=[],
        pages=80,
        user_id="1",
        link=None,
    )
    assert book.link is None


def test_edit_book_change_link(service):
    book = service.create_book(
        title="Edit Change",
        author="Author",
        tags=[],
        pages=60,
        user_id="1",
        link="https://old.com",
    )
    repo = service.book_repo
    book.link = "https://new.com"
    updated = repo.update_book(book)
    assert updated.link == "https://new.com"


def test_edit_book_keep_link(service):
    book = service.create_book(
        title="Keep Link",
        author="Author",
        tags=[],
        pages=70,
        user_id="1",
        link="https://keep.com",
    )
    # Simulate 'keep' by not changing the field
    repo = service.book_repo
    updated = repo.update_book(book)  # no modification
    assert updated.link == "https://keep.com"


def test_edit_book_clear_link(service):
    book = service.create_book(
        title="Clear Link",
        author="Author",
        tags=[],
        pages=50,
        user_id="1",
        link="https://clear.com",
    )
    repo = service.book_repo
    book.link = None
    updated = repo.update_book(book)
    assert updated.link is None
