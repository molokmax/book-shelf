from unittest.mock import patch

from conftest import FakeVkApi as FakeVk
from conftest import make_context

with patch(
    "utils.config.load_config",
    return_value=type("Config", (), {"BOT_TOKEN": "dummy", "data_dir": "data"}),
):
    from vk_bot.handlers.details import DetailsHandler

    handler = DetailsHandler()


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
    with patch("vk_bot.handlers.details.BookService", return_value=FakeBookService(books)):
        handler.handle(ctx)
        assert len(fake_api.sent_messages) == 1
        assert "Какие книги интересуют?" in fake_api.sent_messages[0]["message"]
        handler.handle(ctx)
        assert len(fake_api.sent_messages) == 2
        msg = fake_api.sent_messages[1]["message"]
        assert "1. 📖" in msg and "2. 📎" in msg
        state = ctx.get_state()
        assert state["state"] == "selecting_book"
        assert state["data"]["books"] == ["1", "2"]
