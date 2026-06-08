import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


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
    from vk_bot.handlers.details_handler import DetailsHandler

    handler = DetailsHandler()


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
    def __init__(self, books):
        self._books = books

    def get_book_by_id(self, book_id):
        return next(b for b in self._books if b.id == book_id)

    def get_all_books(self, user_id):
        return self._books


def test_details_counts_today_pages():
    fake_api = FakeVk()
    book = FakeBook(
        id="1",
        title="Today Book",
        author="Author",
        tags=["tag"],
        status=type("S", (), {"value": "reading"}),
        pages=100,
        current_page=20,
        created_at=datetime.now() - timedelta(days=10),
        reading_start_date=datetime.now() - timedelta(days=5),
        link="http://example.com",
    )
    fake_storage = FakeStateStorage()
    fake_storage.save(1, {
        "command": "/details",
        "state": "selecting_book",
        "data": {"books": ["1"]},
    })
    ctx = make_context(fake_api, user_id=1, text="1", storage=fake_storage)
    with patch(
        "vk_bot.handlers.details_handler.BookService", return_value=FakeBookService([book])
    ):
        with patch("vk_bot.handlers.details_handler.ReadingStatsService") as MockStats:
            instance = MockStats.return_value
            instance.get_reading_stats.return_value = 30
            instance.avg_pages_per_day.return_value = 5.0
            instance.predict_completion_date.return_value = None
            handler.handle(ctx)
    assert len(fake_api.sent_messages) == 1
    msg = fake_api.sent_messages[0]["message"]
    assert "30" in msg
