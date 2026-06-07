import json
from unittest.mock import MagicMock, patch


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


# Fake VkApiMethod like in other tests
class FakeVkApiMethod:
    def __init__(self):
        self.sent_messages = []
        self.messages = self

    def send(self, **kwargs):
        self.sent_messages.append(kwargs)


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
        "vk_bot.handlers.list_handler.BookService",
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
        with patch("vk_bot.handlers.list_handler.helpers.sort_books_by_status", lambda b: b):
            with patch(
                "vk_bot.handlers.list_handler.helpers.format_book_info",
                lambda i, b: f"{i}. {b.title} by {b.author}",
            ):
                from vk_bot.handlers.list_handler import ListHandler

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
        "vk_bot.handlers.list_handler.BookService",
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
        with patch("vk_bot.handlers.list_handler.helpers.sort_books_by_status", lambda b: b):
            with patch(
                "vk_bot.handlers.list_handler.helpers.format_book_info",
                lambda i, b: f"{i}. {b.title}",
            ):
                from vk_bot.handlers.list_handler import ListHandler

                handler = ListHandler()
                storage = FakeStateStorage()
                ctx1 = make_context(fake_api, user_id=456, text="По статусу", storage=storage)
                handler.handle(ctx1)
                handler.handle(ctx1)
                ctx2 = make_context(
                    fake_api, user_id=456, text="Читаю", payload={"status": "reading"}, storage=storage
                )
                handler.handle(ctx2)
                last_msg = fake_api.sent_messages[-1]["message"]
                assert "Book One" in last_msg
                assert "Книги со статусом" in last_msg
