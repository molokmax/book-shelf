import pytest
from unittest.mock import patch
from datetime import datetime

from vk_bot.states import active_states

with patch(
    "utils.config.load_config",
    return_value=type("Config", (), {"BOT_TOKEN": "dummy", "data_dir": "data"}),
):
    from vk_bot.handlers.details import handle_details, handle_details_step


# Helper fake VkApiMethod
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
    fake_vk = FakeVk()
    books = [
        FakeBook(id="1", title="Book One", author="A", status="reading"),
        FakeBook(id="2", title="Book Two", author="B", status="want_to_read"),
    ]
    with patch(
        "vk_bot.handlers.details.BookService", return_value=FakeBookService(books)
    ):
        # start command – should ask for filter
        handle_details(fake_vk, user_id=123)
        assert len(fake_vk.sent_messages) == 1
        assert "Какие книги интересуют?" in fake_vk.sent_messages[0]["message"]
        # simulate user choosing "Все"
        handle_details_step(fake_vk, user_id=123, text="Все", payload={})
        # now list should be sent
        assert len(fake_vk.sent_messages) == 2
        msg = fake_vk.sent_messages[1]["message"]
        assert "1. 📖" in msg and "2. 📎" in msg
        # state should be selecting_book with book ids
        assert active_states[123]["state"] == "selecting_book"
        assert active_states[123]["data"]["books"] == ["1", "2"]
