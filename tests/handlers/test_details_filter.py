import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from vk_bot.states import active_states


def make_context(api, user_id, text="", payload=None):
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


with patch(
    "utils.config.load_config",
    return_value=type("Config", (), {"BOT_TOKEN": "dummy", "data_dir": "data"}),
):
    from vk_bot.handlers.details import handle_details, handle_details_step


class FakeVk:
    def __init__(self):
        self.sent_messages = []
        self.messages = self

    def send(self, **kwargs):
        self.sent_messages.append(kwargs)


class FakeBook:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


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


def test_filter_all_path_shows_book_list_and_allows_selection():
    fake_api = FakeVk()
    books = [
        FakeBook(id="1", title="Book One", author="A", status="reading"),
        FakeBook(id="2", title="Book Two", author="B", status="want_to_read"),
    ]
    ctx = make_context(fake_api, user_id=123, text="Все")
    with patch(
        "vk_bot.handlers.details.BookService", return_value=FakeBookService(books)
    ):
        handle_details(ctx)
        assert len(fake_api.sent_messages) == 1
        assert "Какие книги интересуют?" in fake_api.sent_messages[0]["message"]
        handle_details_step(ctx)
        assert len(fake_api.sent_messages) == 2
        msg = fake_api.sent_messages[1]["message"]
        assert "1. 📖" in msg and "2. 📎" in msg
        assert active_states[123]["state"] == "selecting_book"
        assert active_states[123]["data"]["books"] == ["1", "2"]
