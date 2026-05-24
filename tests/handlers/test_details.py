import pytest
from unittest.mock import patch
from datetime import datetime

from vk_bot.states import active_states

with patch("utils.config.load_config", return_value=type('Config', (), {'BOT_TOKEN': 'dummy', 'data_dir': 'data'})):
    from vk_bot.handlers.details import handle_details, handle_details_step


# Helper fake VkApiMethod
class FakeVk:
    def __init__(self):
        self.sent_messages = []
        self.messages = self
        self.users = VkUsers()

    def send(self, user_id, message, keyboard, random_id):
        self.sent_messages.append({
            "user_id": user_id,
            "message": message,
            "keyboard": keyboard,
            "random_id": random_id,
        })


class VkUsers:
    def get(self, user_ids, fields):
        return [{
            'screen_name': 'test_login',
            'first_name': 'test_first_name',
            'last_name': 'test_last_name'
        }]

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
    # Ensure active_states is empty before each test
    active_states.clear()
    yield
    active_states.clear()

def test_handle_details_shows_book_list():
    fake_vk = FakeVk()
    # Prepare two books
    books = [
        FakeBook(id="1", title="Book One", author="Author A", status="reading"),
        FakeBook(id="2", title="Book Two", author="Author B", status="want_to_read"),
    ]
    with patch("vk_bot.handlers.details.BookService", return_value=FakeBookService(books)):
        with patch("core.services.UserService") as MockUserService:
            MockUserService.return_value.get_or_create_user = lambda vk_user_id, user_factory: type('User', (), {'id': str(vk_user_id)})
            handle_details(fake_vk, user_id=123)
    # One message should be sent
    assert len(fake_vk.sent_messages) == 1
    msg = fake_vk.sent_messages[0]["message"]
    print(msg)
    # Verify both titles appear in order with numbers
    assert "1. 📖 Book One" in msg
    assert "2. 📎 Book Two" in msg
    # Verify state is stored for user
    assert 123 in active_states
    assert active_states[123]["command"] == "/details"
    assert active_states[123]["state"] == "selecting_book"
    assert active_states[123]["data"]["books"] == ["1", "2"]

def test_handle_details_step_valid_selection_formats_details():
    fake_vk = FakeVk()
    # Book to be returned by service
    book = FakeBook(
        id="1",
        title="Sample Book",
        author="John Doe",
        tags=["fiction", "mystery"],
        status=type('S', (), {'value': 'reading'} ),
        pages=250,
        current_page=50,
        created_at=datetime(2022, 1, 1),
        reading_start_date=datetime(2022, 1, 5),
        link="https://example.com",
    )
    # Populate state as if user selected details previously
    active_states[456] = {
        "command": "/details",
        "state": "selecting_book",
        "data": {"books": ["1"]},
    }
    with patch("vk_bot.handlers.details.BookService", return_value=FakeBookService([book])) as _book_service:
        with patch("vk_bot.handlers.details.get_status_name", return_value="Читаю") as _status_name:
            from vk_bot.handlers.details import handle_details_step
            handle_details_step(fake_vk, user_id=456, text="1")
    # Should send detailed message
    assert len(fake_vk.sent_messages) == 1
    details_msg = fake_vk.sent_messages[0]["message"]
    assert "Sample Book" in details_msg
    assert "John Doe" in details_msg
    assert "fiction, mystery" in details_msg
    assert "Читаю" in details_msg
    assert "250" in details_msg and "50" in details_msg
    assert "2022-01-01" in details_msg
    assert "2022-01-05" in details_msg
    assert "https://example.com" in details_msg
    # State should be cleared after handling
    assert 456 not in active_states
