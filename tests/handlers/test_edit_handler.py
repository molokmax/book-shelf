import types

import pytest

# Import the module under test
from core.models import ReadingStatus
from vk_bot.handlers import edit

# Helper fake classes

# Additional tests for status filter


def test_choose_status_filter_shows_status_message(monkeypatch):
    vk = FakeVkApiMethod()
    user_id = 777
    edit.handle_edit_command(vk, user_id)
    # Simulate user choosing "по статусу"
    edit.handle_edit_command_step(vk, user_id, "по статусу", {})
    last_msg = vk.sent_messages[-1]
    assert "Выбери статус книги" in last_msg["message"]


def test_status_selection_filters_books_and_shows_list(monkeypatch):
    vk = FakeVkApiMethod()
    user_id = 888
    edit.handle_edit_command(vk, user_id)
    edit.handle_edit_command_step(vk, user_id, "по статусу", {})
    # Simulate selecting a status (payload provides status value; we can pass via payload dict)
    edit.handle_edit_command_step(vk, user_id, "", {"status": "want_to_read"})
    last_msg = vk.sent_messages[-1]
    assert "Введи номер книги" in last_msg["message"]
    assert "Book1" in last_msg["message"]


class FakeVkApiMethod:
    def __init__(self):
        self.sent_messages = []
        self.messages = self

    def send(self, **kwargs):
        self.sent_messages.append(kwargs)


class FakeUser:
    def __init__(self, user_id="test_user"):
        self.id = user_id


# Stub BookService
class StubBookService:
    def __init__(self, *args, **kwargs):
        pass

    def get_all_tags(self, user_id):
        return ["fantasy", "science"]

    def filter_books(self, user_id, status=None, tags=None):
        # Return dummy books
        Book = types.SimpleNamespace
        return [
            Book(
                id="1",
                title="Book1",
                author="Author1",
                tags=[],
                pages=100,
                status=ReadingStatus.WANT_TO_READ,
                link=None,
            )
        ]


# Stub functions from other modules
def fake_get_or_create_user(vk, user_id):
    return FakeUser()


def fake_format_book_info(index, book):
    return f"{index}. {book.title}"


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    # Patch BookService
    monkeypatch.setattr(edit, "BookService", StubBookService)
    # Patch get_or_create_user
    monkeypatch.setattr(edit, "get_or_create_user", fake_get_or_create_user)
    # Patch format_book_info
    monkeypatch.setattr(
        edit, "helpers", types.SimpleNamespace(format_book_info=fake_format_book_info)
    )
    # Ensure active_states is cleared before each test
    edit.active_states.clear()


def test_choose_tag_filter_shows_tags_message():
    vk = FakeVkApiMethod()
    user_id = 123
    # Start edit command
    edit.handle_edit_command(vk, user_id)
    # Simulate user choosing "по тегам"
    edit.handle_edit_command_step(vk, user_id, "по тегам", {})
    # Verify that a message was sent asking to choose a tag
    last_msg = vk.sent_messages[-1]
    assert "Выбери тег" in last_msg["message"]


def test_tag_selection_filters_books_and_shows_list():
    vk = FakeVkApiMethod()
    user_id = 456
    # Start edit command and choose tag mode
    edit.handle_edit_command(vk, user_id)
    edit.handle_edit_command_step(vk, user_id, "по тегам", {})
    # Now simulate selecting a specific tag
    edit.handle_edit_command_step(vk, user_id, "fantasy", {})
    # After selecting tag, a list of books should be sent
    last_msg = vk.sent_messages[-1]
    assert "Введи номер книги" in last_msg["message"]
    # Ensure the book list contains our dummy book title
    assert "Book1" in last_msg["message"]
