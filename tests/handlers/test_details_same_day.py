import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

from vk_bot.states import active_states

with patch(
    "utils.config.load_config",
    return_value=type("Config", (), {"BOT_TOKEN": "dummy", "data_dir": "data"}),
):
    from vk_bot.handlers.details import handle_details_step


# Fake VkApiMethod
class FakeVk:
    def __init__(self):
        self.sent_messages = []
        self.messages = self
        self.users = VkUsers()

    def send(self, user_id, message, keyboard, random_id):
        self.sent_messages.append(
            {
                "user_id": user_id,
                "message": message,
                "keyboard": keyboard,
                "random_id": random_id,
            }
        )


class VkUsers:
    def get(self, user_ids, fields):
        return [{"screen_name": "test", "first_name": "t", "last_name": "t"}]


# Fake book
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
    fake_vk = FakeVk()
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
    # set state as if selected
    active_states[1] = {
        "command": "/details",
        "state": "selecting_book",
        "data": {"books": ["1"]},
    }
    # mock services
    with patch(
        "vk_bot.handlers.details.BookService", return_value=FakeBookService([book])
    ):
        with patch("vk_bot.handlers.details.ReadingStatsService") as MockStats:
            instance = MockStats.return_value
            # simulate today's stats returned as 30 pages
            instance.get_reading_stats.return_value = 30
            instance.avg_pages_per_day.return_value = 5.0
            instance.predict_completion_date.return_value = None
            handle_details_step(fake_vk, user_id=1, text="1", payload={})
    assert len(fake_vk.sent_messages) == 1
    msg = fake_vk.sent_messages[0]["message"]
    assert "30" in msg  # today pages counted
