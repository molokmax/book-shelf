"""Тесты AddHandler: переходы сценария и шаг выбора тегов."""

import json
import types
from unittest.mock import MagicMock

import pytest

from core.models import ACHIEVEMENT_DEFINITIONS
from vk_bot.context import BotContext
from vk_bot.flows import tag_editing as tf
from vk_bot.handlers import add as ah


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
    return BotContext(vk=vk, upload=upload, event=event, storage=storage or FakeStateStorage())


def keyboard_labels(keyboard):
    data = keyboard if isinstance(keyboard, dict) else json.loads(keyboard)
    return [button["action"]["label"] for row in data["buttons"] for button in row]


def keyboard_buttons(keyboard):
    data = keyboard if isinstance(keyboard, dict) else json.loads(keyboard)
    return [button["action"] for row in data["buttons"] for button in row]


class AchievementServiceStub:
    def __init__(self, new_achievements=None, error=None):
        self.new_achievements = new_achievements or []
        self.error = error
        self.checked_user_id = None

    def check(self, user_id):
        self.checked_user_id = user_id
        if self.error:
            raise self.error
        return types.SimpleNamespace(new_achievements=self.new_achievements)


@pytest.fixture(autouse=True)
def stub_achievements(monkeypatch):
    service = AchievementServiceStub()
    monkeypatch.setattr(ah, "AchievementService", lambda: service)
    return service


@pytest.fixture
def saved_books(monkeypatch):
    saved = []

    class StubBookService:
        def create_book(self, **kwargs):
            saved.append(kwargs)
            return types.SimpleNamespace(title=kwargs["title"])

    monkeypatch.setattr(ah, "BookService", StubBookService)
    return saved


@pytest.fixture
def stub_dictionary(monkeypatch):
    """Справочник тегов пользователя для шага выбора тегов."""
    tags = {"list": ["classic", "fantasy"]}

    class StubTagService:
        def get_user_tags(self, user_id):
            return list(tags["list"])

    monkeypatch.setattr(tf, "TagService", StubTagService)
    return tags


def run_manual_flow(fake_api, user_id, storage):
    handler = ah.AddHandler()

    steps = ["/add", "Ручное", "Название", "Автор", "100", "Дальше"]
    for text in steps:
        handler.handle(make_context(fake_api, user_id, text, storage=storage))


def test_manual_flow_opens_tag_step(stub_dictionary, saved_books):
    fake_api = FakeVkApiMethod()
    user_id = 101
    storage = FakeStateStorage()

    run_manual_flow(fake_api, user_id, storage)

    state = storage.get(user_id)
    assert state["state"] == "selecting_tags"
    assert state["data"]["selected_tags"] == []
    assert state["data"]["link"] is None
    message = fake_api.sent_messages[-1]["message"]
    assert "Выбери теги книги" in message
    assert "Готово" in keyboard_labels(fake_api.sent_messages[-1]["keyboard"])
    assert saved_books == []


def test_manual_flow_toggle_and_done_creates_book(stub_dictionary, saved_books):
    fake_api = FakeVkApiMethod()
    user_id = 102
    storage = FakeStateStorage()
    run_manual_flow(fake_api, user_id, storage)

    handler = ah.AddHandler()
    handler.handle(
        make_context(
            fake_api,
            user_id,
            payload={"command": "/add", "action": "toggle", "tag": "fantasy"},
            storage=storage,
        )
    )
    handler.handle(
        make_context(
            fake_api, user_id, payload={"command": "/add", "action": "done"}, storage=storage
        )
    )

    assert len(saved_books) == 1
    created = saved_books[0]
    assert created["tags"] == ["fantasy"]
    assert created["title"] == "Название"
    assert created["link"] is None
    # Пользователь из фикстуры conftest
    assert created["user_id"] == f"user-{user_id}"
    assert "Теги: fantasy" in fake_api.sent_messages[-1]["message"]
    assert storage.get(user_id) == {}
    # Кнопка перехода в главное меню на клавиатуре после добавления книги
    buttons = keyboard_buttons(fake_api.sent_messages[-1]["keyboard"])
    main_menu = [b for b in buttons if b["label"] == "Главное меню"]
    assert len(main_menu) == 1
    assert json.loads(main_menu[0]["payload"]) == {"command": "/back"}


def test_manual_flow_done_without_tags(stub_dictionary, saved_books):
    fake_api = FakeVkApiMethod()
    user_id = 103
    storage = FakeStateStorage()
    run_manual_flow(fake_api, user_id, storage)

    handler = ah.AddHandler()
    handler.handle(
        make_context(
            fake_api, user_id, payload={"command": "/add", "action": "done"}, storage=storage
        )
    )

    assert saved_books[0]["tags"] == []
    assert "Теги: нет" in fake_api.sent_messages[-1]["message"]
    assert storage.get(user_id) == {}


def test_litres_confirm_opens_tag_step(stub_dictionary, saved_books):
    fake_api = FakeVkApiMethod()
    user_id = 104
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/add",
            "state": "waiting_for_litres_confirm",
            "data": {
                "title": "Litres Book",
                "author": "Author",
                "pages": 200,
                "link": "https://litres.ru/book",
            },
        },
    )

    ah.AddHandler().handle(make_context(fake_api, user_id, "Продолжить", storage=storage))

    assert storage.get(user_id)["state"] == "selecting_tags"
    assert saved_books == []


def test_litres_flow_done_creates_book_with_link(stub_dictionary, saved_books):
    fake_api = FakeVkApiMethod()
    user_id = 105
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/add",
            "state": "waiting_for_litres_confirm",
            "data": {
                "title": "Litres Book",
                "author": "Author",
                "pages": 200,
                "link": "https://litres.ru/book",
            },
        },
    )
    handler = ah.AddHandler()
    handler.handle(make_context(fake_api, user_id, "Продолжить", storage=storage))
    handler.handle(
        make_context(
            fake_api, user_id, payload={"command": "/add", "action": "done"}, storage=storage
        )
    )

    created = saved_books[0]
    assert created["link"] == "https://litres.ru/book"
    assert created["tags"] == []
    assert storage.get(user_id) == {}


def test_add_appends_new_achievement(stub_dictionary, saved_books, stub_achievements, monkeypatch):
    service = AchievementServiceStub(new_achievements=[ACHIEVEMENT_DEFINITIONS[0]])
    monkeypatch.setattr(ah, "AchievementService", lambda: service)
    fake_api = FakeVkApiMethod()
    user_id = 106
    storage = FakeStateStorage()
    run_manual_flow(fake_api, user_id, storage)

    ah.AddHandler().handle(
        make_context(
            fake_api, user_id, payload={"command": "/add", "action": "done"}, storage=storage
        )
    )

    assert service.checked_user_id == f"user-{user_id}"
    assert fake_api.sent_messages[-1]["message"].endswith("🏆 Новое достижение: «Первая книга»!")
    assert len(saved_books) == 1


def test_add_without_new_achievement_has_no_achievement_block(stub_dictionary, saved_books):
    fake_api = FakeVkApiMethod()
    user_id = 107
    storage = FakeStateStorage()
    run_manual_flow(fake_api, user_id, storage)

    ah.AddHandler().handle(
        make_context(
            fake_api, user_id, payload={"command": "/add", "action": "done"}, storage=storage
        )
    )

    assert "Новое достижение" not in fake_api.sent_messages[-1]["message"]


def test_add_achievement_error_does_not_block_book_creation(
    stub_dictionary, saved_books, monkeypatch, caplog
):
    service = AchievementServiceStub(error=RuntimeError("achievement storage failed"))
    monkeypatch.setattr(ah, "AchievementService", lambda: service)
    fake_api = FakeVkApiMethod()
    user_id = 108
    storage = FakeStateStorage()
    run_manual_flow(fake_api, user_id, storage)

    ah.AddHandler().handle(
        make_context(
            fake_api, user_id, payload={"command": "/add", "action": "done"}, storage=storage
        )
    )

    assert len(saved_books) == 1
    message = fake_api.sent_messages[-1]["message"]
    assert "успешно добавлена" in message
    assert "Новое достижение" not in message
    assert storage.get(user_id) == {}
    assert "achievement storage failed" in caplog.text
