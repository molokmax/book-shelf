import json
import types

import pytest
from conftest import FakeStateStorage
from conftest import FakeVkApi as FakeVkApiMethod
from conftest import make_context

from core.models import ReadingStatus
from vk_bot.flows import tag_editing as tf
from vk_bot.handlers import edit as eh


class FakeUser:
    def __init__(self, user_id="test_user"):
        self.id = user_id


class StubBookService:
    def __init__(self, *args, **kwargs):
        self.book_repo = types.SimpleNamespace(update_book=lambda book: book)

    def get_all_tags(self, user_id):
        return ["fantasy", "science"]

    def get_book_by_id(self, book_id):
        return types.SimpleNamespace(
            id=book_id,
            title="Book1",
            author="Author1",
            pages=100,
            status=ReadingStatus.READING,
            tags=["old"],
            link=None,
        )

    def filter_books(self, user_id, status=None, tags=None):
        Book = types.SimpleNamespace
        return [
            Book(
                id="1",
                title="Book1",
                author="Author1",
                tags=[],
                pages=100,
                status=ReadingStatus.WANT_TO_READ,
                link=None,
            )
        ]


def fake_get_or_create_user(api, user_id):
    return FakeUser()


def fake_format_book_info(index, book):
    return f"{index}. {book.title}"


@pytest.fixture
def stub_dictionary(monkeypatch):
    """Справочник тегов пользователя для шага выбора тегов."""
    tags = {"list": ["classic", "fantasy"]}

    class StubTagService:
        def get_user_tags(self, user_id):
            return list(tags["list"])

    monkeypatch.setattr(tf, "TagService", StubTagService)
    return tags


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    monkeypatch.setattr(eh, "BookService", StubBookService)
    monkeypatch.setattr(eh, "get_or_create_user", fake_get_or_create_user)
    monkeypatch.setattr(
        eh,
        "helpers",
        types.SimpleNamespace(
            format_book_info=fake_format_book_info,
            sort_books_by_status=lambda books: books,
        ),
    )


def test_choose_status_filter_shows_status_message(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 777
    ctx = make_context(fake_api, user_id, "по статусу")
    eh.EditHandler().handle(ctx)
    eh.EditHandler().handle(ctx)
    last_msg = fake_api.sent_messages[-1]
    assert "Выбери статус книги" in last_msg["message"]


def test_status_selection_filters_books_and_shows_list(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 888
    storage = FakeStateStorage()
    ctx = make_context(fake_api, user_id, "по статусу", storage=storage)
    eh.EditHandler().handle(ctx)
    eh.EditHandler().handle(ctx)
    ctx2 = make_context(fake_api, user_id, "", payload={"status": "want_to_read"}, storage=storage)
    eh.EditHandler().handle(ctx2)
    last_msg = fake_api.sent_messages[-1]
    assert "Введи номер книги" in last_msg["message"]
    assert "Book1" in last_msg["message"]


def test_choose_tag_filter_shows_tags_message():
    fake_api = FakeVkApiMethod()
    user_id = 123
    ctx = make_context(fake_api, user_id, "по тегам")
    eh.EditHandler().handle(ctx)
    eh.EditHandler().handle(ctx)
    last_msg = fake_api.sent_messages[-1]
    assert "Выбери тег" in last_msg["message"]


def test_tag_selection_filters_books_and_shows_list():
    fake_api = FakeVkApiMethod()
    user_id = 456
    storage = FakeStateStorage()
    ctx = make_context(fake_api, user_id, "по тегам", storage=storage)
    eh.EditHandler().handle(ctx)
    eh.EditHandler().handle(ctx)
    ctx2 = make_context(fake_api, user_id, "fantasy", storage=storage)
    eh.EditHandler().handle(ctx2)
    last_msg = fake_api.sent_messages[-1]
    assert "Введи номер книги" in last_msg["message"]
    assert "Book1" in last_msg["message"]


def keyboard_labels(keyboard):
    data = keyboard if isinstance(keyboard, dict) else json.loads(keyboard)
    return [button["action"]["label"] for row in data["buttons"] for button in row]


def test_edit_action_keyboard_has_no_progress_button():
    labels = keyboard_labels(eh.EditHandler._create_book_keyboard().get_keyboard())

    assert "Прогресс" not in labels
    assert "Изменить" in labels
    assert "Статус" in labels
    assert "Удалить" in labels


def test_unknown_action_shows_fallback():
    fake_api = FakeVkApiMethod()
    user_id = 3000
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/edit",
            "state": "selecting_action",
            "data": {"selected_book_id": "1"},
        },
    )
    ctx = make_context(fake_api, user_id, "неизвестно", storage=storage)

    eh.EditHandler().handle(ctx)

    last_msg = fake_api.sent_messages[-1]
    assert last_msg["message"] == "⚠️ Выбери действие"
    assert "Изменить" in keyboard_labels(last_msg["keyboard"])


# ── Шаг выбора тегов ─────────────────────────────────────────────────────────


def test_editing_link_opens_tag_step(stub_dictionary):
    fake_api = FakeVkApiMethod()
    user_id = 4000
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/edit",
            "state": "editing_link",
            "data": {"selected_book_id": "1"},
        },
    )
    ctx = make_context(fake_api, user_id, "Дальше", storage=storage)

    eh.EditHandler().handle(ctx)

    state = storage.get(user_id)
    assert state["state"] == "selecting_tags"
    # Текущие теги книги («old») предвыбраны
    assert state["data"]["selected_tags"] == ["old"]
    message = fake_api.sent_messages[-1]["message"]
    assert "Выбрано: old" in message
    assert "Готово" in keyboard_labels(fake_api.sent_messages[-1]["keyboard"])


def test_tags_toggle_then_done_applies_fields(stub_dictionary):
    fake_api = FakeVkApiMethod()
    user_id = 4001
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/edit",
            "state": "selecting_tags",
            "data": {"selected_book_id": "1"},
        },
    )
    ctx = make_context(
        fake_api,
        user_id,
        payload={"command": "/edit", "action": "toggle", "tag": "fantasy"},
        storage=storage,
    )
    eh.EditHandler().handle(ctx)

    assert storage.get(user_id)["data"]["selected_tags"] == ["fantasy"]

    done = make_context(
        fake_api, user_id, payload={"command": "/edit", "action": "done"}, storage=storage
    )
    eh.EditHandler().handle(done)

    message = fake_api.sent_messages[-1]["message"]
    assert "Книга обновлена: 'Book1' от Author1." in message
    assert "Теги: fantasy" in message
    assert storage.get(user_id) == {}


def test_tags_done_empty_clears_tags(stub_dictionary):
    fake_api = FakeVkApiMethod()
    user_id = 4002
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/edit",
            "state": "selecting_tags",
            "data": {"selected_book_id": "1", "selected_tags": []},
        },
    )
    ctx = make_context(
        fake_api, user_id, payload={"command": "/edit", "action": "done"}, storage=storage
    )

    eh.EditHandler().handle(ctx)

    message = fake_api.sent_messages[-1]["message"]
    assert "Теги: нет" in message
    assert storage.get(user_id) == {}


def test_tags_step_typed_done_confirms(stub_dictionary):
    fake_api = FakeVkApiMethod()
    user_id = 4003
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/edit",
            "state": "selecting_tags",
            "data": {"selected_book_id": "1", "selected_tags": ["fantasy"]},
        },
    )
    ctx = make_context(fake_api, user_id, "готово", storage=storage)

    eh.EditHandler().handle(ctx)

    assert "Теги: fantasy" in fake_api.sent_messages[-1]["message"]
    assert storage.get(user_id) == {}


def test_tags_step_invalid_typed_input_stays(stub_dictionary):
    fake_api = FakeVkApiMethod()
    user_id = 4004
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/edit",
            "state": "selecting_tags",
            "data": {"selected_book_id": "1", "selected_tags": []},
        },
    )
    ctx = make_context(fake_api, user_id, " , ", storage=storage)

    eh.EditHandler().handle(ctx)

    assert "Не удалось обработать сообщение" in fake_api.sent_messages[-1]["message"]
    assert storage.get(user_id)["state"] == "selecting_tags"
