from unittest.mock import patch

from conftest import FakeStateStorage
from conftest import FakeVkApi as FakeVkApiMethod
from conftest import make_context


# Fake book objects
class FakeBook:
    def __init__(self, title, author, status, tags=None):
        self.title = title
        self.author = author
        self.status = status
        self.tags = tags or []
        self.id = "1"


# Helper patches will provide required functions


def test_handle_list_flow_all_books():
    fake_api = FakeVkApiMethod()
    books = [
        FakeBook("Book One", "Author A", type("S", (), {"value": "reading"})),
        FakeBook("Book Two", "Author B", type("S", (), {"value": "want_to_read"})),
    ]
    with patch(
        "vk_bot.handlers.list.BookService",
        return_value=type(
            "Svc",
            (),
            {
                "get_all_books": lambda self, str: books,
                "filter_books": lambda self, str, **kwargs: books,
                "get_all_tags": lambda self: [],
            },
        )(),
    ):
        with patch("vk_bot.handlers.list.helpers.sort_books_by_status", lambda b: b):
            with patch(
                "vk_bot.handlers.list.helpers.format_book_info",
                lambda i, b: f"{i}. {b.title} by {b.author}",
            ):
                from vk_bot.handlers.list import ListHandler

                handler = ListHandler()
                ctx = make_context(fake_api, user_id=123, text="Все")
                handler.handle(ctx)
                assert ctx.is_active()
                assert fake_api.sent_messages[-1]["message"] == "Какие книги интересуют?"
                handler.handle(ctx)
                last_msg = fake_api.sent_messages[-1]["message"]
                assert "Book One" in last_msg and "Book Two" in last_msg
                assert not ctx.is_active()


def test_handle_list_flow_by_status():
    fake_api = FakeVkApiMethod()
    book = FakeBook("Book One", "Author A", type("S", (), {"value": "reading"}))
    with patch(
        "vk_bot.handlers.list.BookService",
        return_value=type(
            "Svc",
            (),
            {
                "filter_books": lambda self, str, status=None, tags=None: (
                    [book] if status == "reading" else []
                ),
                "get_all_tags": lambda self: [],
            },
        )(),
    ):
        with patch("vk_bot.handlers.list.helpers.sort_books_by_status", lambda b: b):
            with patch(
                "vk_bot.handlers.list.helpers.format_book_info",
                lambda i, b: f"{i}. {b.title}",
            ):
                from vk_bot.handlers.list import ListHandler

                handler = ListHandler()
                storage = FakeStateStorage()
                ctx1 = make_context(fake_api, user_id=456, text="По статусу", storage=storage)
                handler.handle(ctx1)
                handler.handle(ctx1)
                ctx2 = make_context(
                    fake_api,
                    user_id=456,
                    text="Читаю",
                    payload={"status": "reading"},
                    storage=storage,
                )
                handler.handle(ctx2)
                last_msg = fake_api.sent_messages[-1]["message"]
                assert "Book One" in last_msg
                assert "Книги со статусом" in last_msg
