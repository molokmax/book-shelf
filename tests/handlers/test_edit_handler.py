import json
import types
from unittest.mock import MagicMock

import pytest

# Import the module under test
from core.models import ReadingStatus
from vk_bot.handlers import edit

# Helper to create BotContext for tests


def make_context(api, user_id, text="", payload=None):
    import json
    vk = MagicMock()
    vk.get_api.return_value = api
    upload = MagicMock()
    event = MagicMock()
    event.user_id = user_id
    event.peer_id = user_id
    event.text = text
    event.payload = json.dumps(payload) if payload else None
    from vk_bot.context import BotContext

    return BotContext(vk=vk, upload=upload, event=event)


# Additional tests for status filter


def test_choose_status_filter_shows_status_message(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 777
    ctx = make_context(fake_api, user_id, "по статусу")
    edit.handle_edit_command(ctx)
    # Simulate user choosing "по статусу"
    edit.handle_edit_command_step(ctx)
    last_msg = fake_api.sent_messages[-1]
    assert "Выбери статус книги" in last_msg["message"]


def test_status_selection_filters_books_and_shows_list(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 888
    ctx = make_context(fake_api, user_id, "по статусу")
    edit.handle_edit_command(ctx)
    edit.handle_edit_command_step(ctx)
    # Simulate selecting a status
    ctx2 = make_context(fake_api, user_id, "", payload={"status": "want_to_read"})
    edit.handle_edit_command_step(ctx2)
    last_msg = fake_api.sent_messages[-1]
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
def fake_get_or_create_user(api, user_id):
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
    fake_api = FakeVkApiMethod()
    user_id = 123
    ctx = make_context(fake_api, user_id, "по тегам")
    # Start edit command
    edit.handle_edit_command(ctx)
    # Simulate user choosing "по тегам"
    edit.handle_edit_command_step(ctx)
    # Verify that a message was sent asking to choose a tag
    last_msg = fake_api.sent_messages[-1]
    assert "Выбери тег" in last_msg["message"]


def test_tag_selection_filters_books_and_shows_list():
    fake_api = FakeVkApiMethod()
    user_id = 456
    ctx = make_context(fake_api, user_id, "по тегам")
    # Start edit command and choose tag mode
    edit.handle_edit_command(ctx)
    edit.handle_edit_command_step(ctx)
    # Now simulate selecting a specific tag
    ctx2 = make_context(fake_api, user_id, "fantasy")
    edit.handle_edit_command_step(ctx2)
    # After selecting tag, a list of books should be sent
    last_msg = fake_api.sent_messages[-1]
    assert "Введи номер книги" in last_msg["message"]
    # Ensure the book list contains our dummy book title
    assert "Book1" in last_msg["message"]
