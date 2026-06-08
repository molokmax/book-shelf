import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


class FakeStateStorage:
    def __init__(self):
        self._data = {}

    def get(self, user_id):
        return self._data.get(user_id, {})

    def save(self, user_id, state):
        self._data[user_id] = state

    def delete(self, user_id):
        self._data.pop(user_id, None)

    def is_active(self, user_id):
        return bool(self._data.get(user_id))

    def get_command(self, user_id):
        state = self._data.get(user_id)
        return state.get("command") if state else None

    def get_current_state(self, user_id):
        state = self._data.get(user_id)
        return state.get("state") if state else None


def make_context(api, user_id, text="", payload=None, storage=None):
    vk = MagicMock()
    vk.get_api.return_value = api
    upload = MagicMock()
    event = MagicMock()
    event.user_id = user_id
    event.peer_id = user_id
    event.text = text
    event.payload = json.dumps(payload) if payload else None
    from vk_bot.context import BotContext

    return BotContext(vk=vk, upload=upload, event=event, storage=storage or FakeStateStorage())


with patch(
    "utils.config.load_config",
    return_value=type("Config", (), {"BOT_TOKEN": "dummy", "data_dir": "data"}),
):
    from vk_bot.handlers.details import DetailsHandler

    handler = DetailsHandler()


# Helper fake VkApiMethod
class FakeVk:
    def __init__(self):
        self.sent_messages = []
        self.messages = self

    def send(self, **kwargs):
        self.sent_messages.append(kwargs)


# Fake book object
class FakeBook:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# Fake BookService
class FakeBookService:
    def __init__(self, books=None):
        self._books = books or []

    def get_all_books(self, user_id):
        return self._books

    def get_book_by_id(self, book_id):
        for b in self._books:
            if b.id == book_id:
                return b
        return None


@pytest.fixture(autouse=True)
def clear_state():
    yield


def test_handle_details_shows_book_list():
    fake_api = FakeVk()
    books = [
        FakeBook(id="1", title="Book One", author="Author A", status="reading"),
        FakeBook(id="2", title="Book Two", author="Author B", status="want_to_read"),
    ]
    with patch(
        "vk_bot.handlers.details.BookService", return_value=FakeBookService(books)
    ):
        with patch("core.services.UserService") as MockUserService:
            MockUserService.return_value.get_or_create_user = (
                lambda vk_user_id, user_factory: type(
                    "User", (), {"id": str(vk_user_id)}
                )
            )
            ctx = make_context(fake_api, user_id=123, text="Все")
            handler.handle(ctx)
            assert len(fake_api.sent_messages) == 1
            msg = fake_api.sent_messages[0]["message"]
            assert msg == "Какие книги интересуют?"
            fake_api.sent_messages.clear()
            state = ctx.get_state()
            assert state["state"] == "choose_filter"
            handler.handle(ctx)
    assert len(fake_api.sent_messages) == 1
    list_msg = fake_api.sent_messages[0]["message"]
    assert "1. 📖 Book One" in list_msg
    assert "2. 📎 Book Two" in list_msg
    state = ctx.get_state()
    assert state["state"] == "selecting_book"
    assert state["data"]["books"] == ["1", "2"]


def test_handle_details_step_valid_selection_formats_details():
    fake_api = FakeVk()
    book = FakeBook(
        id="1",
        title="Sample Book",
        author="John Doe",
        tags=["fiction", "mystery"],
        status=type("S", (), {"value": "reading"}),
        pages=250,
        current_page=50,
        created_at=datetime(2022, 1, 1),
        reading_start_date=datetime(2022, 1, 5),
        link="https://example.com",
    )
    fake_storage = FakeStateStorage()
    fake_storage.save(456, {
        "command": "/details",
        "state": "selecting_book",
        "data": {"books": ["1"]},
    })
    ctx = make_context(fake_api, user_id=456, text="1", storage=fake_storage)
    with patch(
        "vk_bot.handlers.details.BookService", return_value=FakeBookService([book])
    ) as _book_service:
        handler.handle(ctx)
    assert len(fake_api.sent_messages) == 1
    details_msg = fake_api.sent_messages[0]["message"]
    assert "Sample Book" in details_msg
    assert "John Doe" in details_msg
    assert "fiction, mystery" in details_msg
    assert "Читаю" in details_msg
    assert "250" in details_msg and "50" in details_msg
    assert "2022-01-01" in details_msg
    assert "2022-01-05" in details_msg
    assert "https://example.com" in details_msg
    assert not fake_storage.is_active(456)
