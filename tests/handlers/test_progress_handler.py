import json
import types
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from core.models import ReadingStatus
from vk_bot.command_router import CommandRouter
from vk_bot.flows import book_selection as bsf
from vk_bot.handlers import progress as ph
from vk_bot.handlers.base import AbstractCommandHandler


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


class FakeVkApiMethod:
    def __init__(self):
        self.sent_messages = []
        self.messages = self

    def send(self, **kwargs):
        self.sent_messages.append(kwargs)


class FakeUser:
    def __init__(self, user_id="test_user"):
        self.id = user_id


def make_book(book_id="1", title="Book1", current_page=55, pages=319, updated_at=None):
    return types.SimpleNamespace(
        id=book_id,
        title=title,
        author="Author",
        tags=[],
        pages=pages,
        current_page=current_page,
        status=ReadingStatus.READING,
        link=None,
        updated_at=updated_at or datetime(2026, 1, 1),
    )


class StubBookService:
    def __init__(
        self,
        reading_books=None,
        filtered_books=None,
        all_books=None,
        tags=None,
        book_by_id=None,
    ):
        self.reading_books = reading_books or []
        self.filtered_books = filtered_books or []
        self.all_books = all_books or []
        self.tags = tags or []
        self.book_by_id = book_by_id or {}

    def filter_books(self, user_id, status=None, tags=None):
        if self.filtered_books:
            return self.filtered_books
        if status == ReadingStatus.READING.value:
            return self.reading_books
        return []

    def get_all_books(self, user_id):
        return self.all_books

    def get_all_tags(self, user_id):
        return self.tags

    def get_book_by_id(self, book_id):
        return self.book_by_id.get(book_id)


def keyboard_labels(keyboard):
    data = keyboard if isinstance(keyboard, dict) else json.loads(keyboard)
    return [button["action"]["label"] for row in data["buttons"] for button in row]


@pytest.fixture(autouse=True)
def patch_user(monkeypatch):
    monkeypatch.setattr(ph, "get_or_create_user", lambda api, user_id: FakeUser())
    monkeypatch.setattr(bsf, "get_or_create_user", lambda api, user_id: FakeUser())


def test_entry_shows_reading_books(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 1
    storage = FakeStateStorage()
    older = make_book("1", "Book1", updated_at=datetime(2026, 1, 1))
    newer = make_book("2", "Book2", updated_at=datetime(2026, 1, 2))
    monkeypatch.setattr(
        ph,
        "BookService",
        lambda: StubBookService(reading_books=[older, newer]),
    )

    ctx = make_context(fake_api, user_id, "/progress", storage=storage)
    ph.ProgressHandler().handle(ctx)

    last_msg = fake_api.sent_messages[-1]
    assert "Введи номер книги для обновления прогресса" in last_msg["message"]
    assert "Book1" in last_msg["message"]
    assert "Book2" in last_msg["message"]
    assert "Другие" in keyboard_labels(last_msg["keyboard"])
    assert storage.get(user_id)["state"] == "selecting_reading_book"
    assert storage.get(user_id)["data"]["books"] == ["2", "1"]


def test_empty_reading_list_opens_filter(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 2
    storage = FakeStateStorage()
    monkeypatch.setattr(ph, "BookService", lambda: StubBookService(reading_books=[]))

    ctx = make_context(fake_api, user_id, "/progress", storage=storage)
    ph.ProgressHandler().handle(ctx)

    last_msg = fake_api.sent_messages[-1]
    assert "Нет книг в статусе «Читаю»" in last_msg["message"]
    assert "По статусу" in keyboard_labels(last_msg["keyboard"])
    assert storage.get(user_id)["state"] == "choose_filter"


def test_other_button_opens_filter(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 3
    storage = FakeStateStorage()
    book = make_book()
    monkeypatch.setattr(
        ph,
        "BookService",
        lambda: StubBookService(reading_books=[book], book_by_id={"1": book}),
    )
    ctx = make_context(fake_api, user_id, "/progress", storage=storage)
    ph.ProgressHandler().handle(ctx)

    ctx2 = make_context(fake_api, user_id, "Другие", storage=storage)
    ph.ProgressHandler().handle(ctx2)

    last_msg = fake_api.sent_messages[-1]
    assert last_msg["message"] == "Какие книги интересуют?"
    assert "По тегам" in keyboard_labels(last_msg["keyboard"])
    assert storage.get(user_id)["state"] == "choose_filter"


def test_select_reading_book_opens_progress_prompt(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 4
    storage = FakeStateStorage()
    book = make_book(current_page=55, pages=319)
    monkeypatch.setattr(
        ph,
        "BookService",
        lambda: StubBookService(reading_books=[book], book_by_id={"1": book}),
    )
    ctx = make_context(fake_api, user_id, "/progress", storage=storage)
    ph.ProgressHandler().handle(ctx)

    ctx2 = make_context(fake_api, user_id, "1", storage=storage)
    ph.ProgressHandler().handle(ctx2)

    last_msg = fake_api.sent_messages[-1]
    assert "📖 Книга: Book1" in last_msg["message"]
    assert "Прогресс: 55/319 (17%)" in last_msg["message"]
    assert "Введи текущую страницу" in last_msg["message"]
    assert storage.get(user_id)["state"] == "waiting_for_progress_input"


def test_status_filter_shows_books(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 5
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {"command": "/progress", "state": "choose_filter", "data": {"user_id": "u1"}},
    )
    book = make_book()
    monkeypatch.setattr(
        bsf,
        "BookService",
        lambda: StubBookService(filtered_books=[book]),
    )

    ctx = make_context(fake_api, user_id, "По статусу", storage=storage)
    ph.ProgressHandler().handle(ctx)
    assert "Выбери статус книги" in fake_api.sent_messages[-1]["message"]

    ctx2 = make_context(fake_api, user_id, "", payload={"status": "reading"}, storage=storage)
    ph.ProgressHandler().handle(ctx2)

    last_msg = fake_api.sent_messages[-1]
    assert "Введи номер книги" in last_msg["message"]
    assert "Book1" in last_msg["message"]
    assert storage.get(user_id)["state"] == "selecting_book"


def test_status_filter_without_payload_uses_standard_message():
    fake_api = FakeVkApiMethod()
    user_id = 50
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/progress",
            "state": "selecting_status_filter",
            "data": {"user_id": "u1"},
        },
    )

    ctx = make_context(fake_api, user_id, "что-то", storage=storage)
    ph.ProgressHandler().handle(ctx)

    last_msg = fake_api.sent_messages[-1]
    assert last_msg["message"].startswith("⚠️ Не удалось обработать сообщение.")
    assert "Выбери статус из клавиатуры" in last_msg["message"]
    assert storage.get(user_id)["state"] == "selecting_status_filter"


def test_tag_filter_shows_books(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 6
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {"command": "/progress", "state": "choose_filter", "data": {"user_id": "u1"}},
    )
    book = make_book()
    monkeypatch.setattr(
        bsf,
        "BookService",
        lambda: StubBookService(filtered_books=[book], tags=["fantasy"]),
    )

    ctx = make_context(fake_api, user_id, "По тегам", storage=storage)
    ph.ProgressHandler().handle(ctx)
    assert "Выбери тег" in fake_api.sent_messages[-1]["message"]

    ctx2 = make_context(fake_api, user_id, "fantasy", storage=storage)
    ph.ProgressHandler().handle(ctx2)

    last_msg = fake_api.sent_messages[-1]
    assert "Книги с выбранным тегом" in last_msg["message"]
    assert "Book1" in last_msg["message"]


def test_all_filter_shows_books(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 7
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {"command": "/progress", "state": "choose_filter", "data": {"user_id": "u1"}},
    )
    book = make_book()
    monkeypatch.setattr(
        bsf,
        "BookService",
        lambda: StubBookService(all_books=[book]),
    )

    ctx = make_context(fake_api, user_id, "Все", storage=storage)
    ph.ProgressHandler().handle(ctx)

    last_msg = fake_api.sent_messages[-1]
    assert "Твоя библиотека" in last_msg["message"]
    assert "Book1" in last_msg["message"]


def test_empty_filter_result_returns_to_main(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 51
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/progress",
            "state": "selecting_status_filter",
            "data": {"user_id": "u1"},
        },
    )
    monkeypatch.setattr(
        bsf,
        "BookService",
        lambda: StubBookService(filtered_books=[]),
    )

    ctx = make_context(fake_api, user_id, "", payload={"status": "reading"}, storage=storage)
    ph.ProgressHandler().handle(ctx)

    last_msg = fake_api.sent_messages[-1]
    assert last_msg["message"] == "Книг с выбранным статусом нет."
    assert not storage.is_active(user_id)


def test_main_keyboard_contains_progress_command():
    from vk_bot.keyboards import main_keyboard

    labels = keyboard_labels(main_keyboard().get_keyboard())

    assert labels[:3] == ["/progress", "/edit", "/add"]
    assert labels[3:6] == ["/list", "/details", "/export"]
    assert labels[6:] == ["/stats", "/help"]


def test_select_book_from_filter_opens_progress_prompt(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 8
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/progress",
            "state": "selecting_book",
            "data": {"user_id": "u1", "books": ["1"]},
        },
    )
    book = make_book()
    monkeypatch.setattr(
        bsf,
        "BookService",
        lambda: StubBookService(book_by_id={"1": book}),
    )

    ctx = make_context(fake_api, user_id, "1", storage=storage)
    ph.ProgressHandler().handle(ctx)

    last_msg = fake_api.sent_messages[-1]
    assert "📖 Книга: Book1" in last_msg["message"]
    assert storage.get(user_id)["state"] == "waiting_for_progress_input"


def test_invalid_reading_book_selection_uses_standard_message(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 9
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/progress",
            "state": "selecting_reading_book",
            "data": {"user_id": "u1", "books": ["1"]},
        },
    )

    ctx = make_context(fake_api, user_id, "abc", storage=storage)
    ph.ProgressHandler().handle(ctx)

    last_msg = fake_api.sent_messages[-1]
    assert last_msg["message"].startswith("⚠️ Не удалось обработать сообщение.")
    assert "Введи корректный номер книги" in last_msg["message"]
    assert storage.get(user_id)["state"] == "selecting_reading_book"


def test_invalid_filter_choice_uses_standard_message():
    fake_api = FakeVkApiMethod()
    user_id = 10
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {"command": "/progress", "state": "choose_filter", "data": {"user_id": "u1"}},
    )

    ctx = make_context(fake_api, user_id, "abc", storage=storage)
    ph.ProgressHandler().handle(ctx)

    last_msg = fake_api.sent_messages[-1]
    assert last_msg["message"].startswith("⚠️ Не удалось обработать сообщение.")
    assert "По статусу" in last_msg["message"]
    assert storage.get(user_id)["state"] == "choose_filter"


def test_repeated_progress_command_is_invalid_input():
    fake_api = FakeVkApiMethod()
    user_id = 11
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/progress",
            "state": "waiting_for_progress_input",
            "data": {"selected_book_id": "1", "progress_book_pages": 319},
        },
    )

    ctx = make_context(fake_api, user_id, "/progress", storage=storage)
    ph.ProgressHandler().handle(ctx)

    last_msg = fake_api.sent_messages[-1]
    assert last_msg["message"].startswith("⚠️ Не удалось обработать сообщение.")
    assert "Введи число" in last_msg["message"]
    assert storage.get(user_id)["state"] == "waiting_for_progress_input"


def test_progress_handler_declines_other_active_state():
    fake_api = FakeVkApiMethod()
    user_id = 12
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {"command": "/add", "state": "waiting_for_title", "data": {}},
    )

    ctx = make_context(fake_api, user_id, "/progress", storage=storage)
    result = ph.ProgressHandler().handle(ctx)

    assert result is None
    assert fake_api.sent_messages == []
    assert storage.get(user_id)["state"] == "waiting_for_title"


def test_router_falls_back_to_active_handler(monkeypatch):
    class ActiveHandler(AbstractCommandHandler):
        priority = 10
        commands = ["/add"]

        def __init__(self):
            self.called = False

        def handle(self, context):
            self.called = True
            return "active handled"

    monkeypatch.setattr("vk_bot.command_router.load_config", lambda: types.SimpleNamespace())
    active_handler = ActiveHandler()
    router = CommandRouter()
    router.register_handler(ph.ProgressHandler())
    router.register_handler(active_handler)

    storage = FakeStateStorage()
    storage.save(1, {"command": "/add", "state": "waiting_for_title", "data": {}})
    ctx = make_context(FakeVkApiMethod(), 1, "/progress", storage=storage)

    result = router.route(ctx)

    assert result == "active handled"
    assert active_handler.called is True
