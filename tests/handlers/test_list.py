from unittest.mock import patch


# Fake VkApiMethod like in other tests
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
        return [{"screen_name": "test", "first_name": "Test", "last_name": "User"}]


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
    fake_vk = FakeVk()
    # Prepare fake books
    books = [
        FakeBook("Book One", "Author A", type("S", (), {"value": "reading"})),
        FakeBook("Book Two", "Author B", type("S", (), {"value": "want_to_read"})),
    ]
    # Patch dependencies
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
                from vk_bot.handlers.list import (
                    handle_list_command,
                    handle_list_command_step,
                )

                # Start command
                handle_list_command(fake_vk, user_id=123)
                # Verify state stored and filter keyboard sent
                assert 123 in __import__("vk_bot.states").states.active_states
                assert fake_vk.sent_messages[-1]["message"] == "Какие книги интересуют?"
                # Simulate choosing "Все"
                handle_list_command_step(fake_vk, user_id=123, text="Все", payload={})
                # Last message should contain list of books
                last_msg = fake_vk.sent_messages[-1]["message"]
                assert "Book One" in last_msg and "Book Two" in last_msg
                # State should be cleared after finishing
                assert 123 not in __import__("vk_bot.states").states.active_states


def test_handle_list_flow_by_status():
    fake_vk = FakeVk()
    # Book with status reading
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
                from vk_bot.handlers.list import (
                    handle_list_command,
                    handle_list_command_step,
                )

                handle_list_command(fake_vk, user_id=456)
                handle_list_command_step(
                    fake_vk, user_id=456, text="По статусу", payload={}
                )
                # Choose status "reading"
                handle_list_command_step(
                    fake_vk, user_id=456, text="Читаю", payload={"status": "reading"}
                )
                last_msg = fake_vk.sent_messages[-1]["message"]
                assert "Book One" in last_msg
                assert "Книги со статусом" in last_msg
