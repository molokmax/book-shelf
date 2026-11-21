"""Сквозные тесты кнопки «Назад» (issue #59) для сценариев команд."""

import json
import types
from datetime import datetime

import pytest
from conftest import FakeStateStorage
from conftest import FakeVkApi as FakeVkApiMethod
from conftest import make_context

from core.models import ReadingStatus
from vk_bot.flows import book_selection as bsf
from vk_bot.flows import progress_update as puf
from vk_bot.flows import tag_editing as tf
from vk_bot.handlers import add as ah
from vk_bot.handlers import details as dh
from vk_bot.handlers import edit as eh
from vk_bot.handlers import goal as gh
from vk_bot.handlers import list as lh
from vk_bot.handlers import progress as ph


def keyboard_labels(keyboard):
    data = keyboard if isinstance(keyboard, dict) else json.loads(keyboard)
    return [button["action"]["label"] for row in data["buttons"] for button in row]


def back_context(api, storage, command, user_id=1):
    return make_context(
        api,
        user_id,
        "",
        payload={"command": command, "action": "back"},
        storage=storage,
    )


def seed_state(storage, command, state, data=None, history=None, user_id=1):
    storage.save(
        user_id,
        {
            "command": command,
            "state": state,
            "data": data or {},
            "history": history or [],
        },
    )


def make_book(book_id="1", title="Book1", current_page=55, pages=319):
    return types.SimpleNamespace(
        id=book_id,
        title=title,
        author="Author",
        tags=[],
        pages=pages,
        current_page=current_page,
        status=ReadingStatus.READING,
        link=None,
        updated_at=datetime(2026, 1, 1),
    )


class StubBookService:
    """Заглушка BookService: любая запись в тестах «Назад» запрещена."""

    def __init__(self, reading_books=None, book_by_id=None):
        self.reading_books = reading_books or []
        self.book_by_id = book_by_id or {}

    def filter_books(self, user_id, status=None, tags=None):
        if status == ReadingStatus.READING.value:
            return self.reading_books
        return []

    def get_book_by_id(self, book_id):
        return self.book_by_id.get(book_id)

    def get_all_tags(self, user_id):
        return []

    def update_book_progress(self, *args, **kwargs):
        raise AssertionError("«Назад» не должен обновлять прогресс")

    def update_book_status(self, *args, **kwargs):
        raise AssertionError("«Назад» не должен менять статус")

    def create_book(self, **kwargs):
        raise AssertionError("«Назад» не должен создавать книгу")


@pytest.fixture
def stub_tags(monkeypatch):
    class StubTagService:
        def get_user_tags(self, user_id):
            return ["classic", "fantasy"]

    monkeypatch.setattr(tf, "TagService", StubTagService)


# ── /add ────────────────────────────────────────────────────────────


def test_add_back_from_tags_returns_to_link_and_resets_tags(stub_tags):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    handler = ah.AddHandler()

    for text in ["/add", "Ручное", "Название", "Автор", "100", "Дальше"]:
        handler.handle(make_context(fake_api, 1, text, storage=storage))
    assert storage.get(1)["state"] == "selecting_tags"

    handler.handle(back_context(fake_api, storage, "/add"))

    state = storage.get(1)
    assert state["state"] == "waiting_for_link"
    assert "selected_tags" not in state["data"]
    assert state["data"]["title"] == "Название"
    last_msg = fake_api.sent_messages[-1]
    assert "ссылку на книгу" in last_msg["message"]
    assert "Назад" in keyboard_labels(last_msg["keyboard"])

    # Повторный проход: шаг тегов начинается с чистого листа
    handler.handle(make_context(fake_api, 1, "Дальше", storage=storage))
    assert storage.get(1)["state"] == "selecting_tags"
    assert storage.get(1)["data"]["selected_tags"] == []


def test_add_back_from_tags_returns_to_litres_confirm():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    seed_state(
        storage,
        "/add",
        "selecting_tags",
        data={"title": "T", "selected_tags": ["x"], "tag_page": 0},
        history=[
            {
                "state": "waiting_for_litres_confirm",
                "data": {"title": "T", "author": "A", "pages": 100, "link": "u"},
            }
        ],
    )

    ah.AddHandler().handle(back_context(fake_api, storage, "/add"))

    state = storage.get(1)
    assert state["state"] == "waiting_for_litres_confirm"
    assert "selected_tags" not in state["data"]
    message = fake_api.sent_messages[-1]["message"]
    assert "Найдены данные книги" in message
    assert "Название: T" in message


def test_add_back_to_first_step_hides_back_button():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    handler = ah.AddHandler()

    handler.handle(make_context(fake_api, 1, "/add", storage=storage))
    handler.handle(make_context(fake_api, 1, "Ручное", storage=storage))
    handler.handle(back_context(fake_api, storage, "/add"))

    assert storage.get(1)["state"] == "choose_method"
    last_msg = fake_api.sent_messages[-1]
    assert "Выбери способ добавления" in last_msg["message"]
    assert "Назад" not in keyboard_labels(last_msg["keyboard"])


# ── /edit ───────────────────────────────────────────────────────────


def test_edit_back_from_status_to_action():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    seed_state(
        storage,
        "/edit",
        "selecting_status",
        data={"selected_book_id": "1", "selected_book_title": "T"},
        history=[
            {
                "state": "selecting_action",
                "data": {"selected_book_id": "1", "selected_book_title": "T"},
            }
        ],
    )

    eh.EditHandler().handle(back_context(fake_api, storage, "/edit"))

    assert storage.get(1)["state"] == "selecting_action"
    assert "Выбрана книга 'T'" in fake_api.sent_messages[-1]["message"]


def test_edit_back_from_tags_to_editing_link(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    book = make_book()
    seed_state(
        storage,
        "/edit",
        "selecting_tags",
        data={"selected_book_id": "1", "selected_tags": ["x"]},
        history=[{"state": "editing_link", "data": {"selected_book_id": "1"}}],
    )
    monkeypatch.setattr(eh, "BookService", lambda: StubBookService(book_by_id={"1": book}))

    eh.EditHandler().handle(back_context(fake_api, storage, "/edit"))

    assert storage.get(1)["state"] == "editing_link"
    assert "Текущая ссылка" in fake_api.sent_messages[-1]["message"]


def test_edit_back_from_action_to_book_list():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    seed_state(
        storage,
        "/edit",
        "selecting_action",
        data={"selected_book_id": "1", "selected_book_title": "T"},
        history=[
            {
                "state": "selecting_book",
                "data": {"books": ["1"], "list_header": "H\n", "book_lines": ["line\n"]},
            }
        ],
    )

    eh.EditHandler().handle(back_context(fake_api, storage, "/edit"))

    assert storage.get(1)["state"] == "selecting_book"
    assert fake_api.sent_messages[-1]["message"] == "H\nline\n"


# ── /details ────────────────────────────────────────────────────────


def test_details_back_from_book_list_to_filter():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    seed_state(
        storage,
        "/details",
        "selecting_book",
        data={"books": ["1"], "list_header": "H\n", "book_lines": ["line\n"]},
        history=[{"state": "choose_filter", "data": {}}],
    )

    dh.DetailsHandler().handle(back_context(fake_api, storage, "/details"))

    assert storage.get(1)["state"] == "choose_filter"
    last_msg = fake_api.sent_messages[-1]
    assert last_msg["message"] == "Какие книги интересуют?"
    assert "Назад" not in keyboard_labels(last_msg["keyboard"])


# ── /list ───────────────────────────────────────────────────────────


def test_list_back_from_status_to_filter():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    handler = lh.ListHandler()

    handler.handle(make_context(fake_api, 1, "/list", storage=storage))
    handler.handle(make_context(fake_api, 1, "По статусу", storage=storage))
    assert storage.get(1)["state"] == "choose_status"
    assert "Назад" in keyboard_labels(fake_api.sent_messages[-1]["keyboard"])

    handler.handle(back_context(fake_api, storage, "/list"))

    assert storage.get(1)["state"] == "choose_filter"
    last_msg = fake_api.sent_messages[-1]
    assert last_msg["message"] == "Какие книги интересуют?"
    assert "Назад" not in keyboard_labels(last_msg["keyboard"])


# ── /goal ───────────────────────────────────────────────────────────


def test_goal_back_from_input_to_menu_without_saving(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    class ReadableGoalService:
        def __init__(self):
            self.pages_today = 35

        def get_goal_status(self, user_id):
            return types.SimpleNamespace(
                goal=types.SimpleNamespace(target=50),
                pages_today=self.pages_today,
                percent=round(self.pages_today / 50 * 100),
                completed=False,
                remaining=50 - self.pages_today,
            )

        def set_daily_goal(self, user_id, target):
            raise AssertionError("«Назад» не должно устанавливать цель")

        def disable_goal(self, user_id):
            raise AssertionError("«Назад» не должно отключать цель")

    service = ReadableGoalService()
    monkeypatch.setattr(gh, "GoalService", lambda: service)
    handler = gh.GoalHandler()

    handler.handle(make_context(fake_api, 1, "/goal", storage=storage))
    assert "Сегодня прочитано: 35 стр. (70%)" in fake_api.sent_messages[-1]["message"]
    handler.handle(make_context(fake_api, 1, "Установить", storage=storage))
    assert storage.get(1)["state"] == "waiting_for_goal_input"

    service.pages_today = 40
    handler.handle(back_context(fake_api, storage, "/goal"))

    assert storage.get(1)["state"] == "menu"
    message = fake_api.sent_messages[-1]["message"]
    assert "Сегодня прочитано: 40 стр. (80%)" in message
    assert "Осталось: 10 стр." in message
    assert "Выбери действие" in message


# ── /progress ───────────────────────────────────────────────────────


def test_progress_back_from_input_to_reading_list(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    book = make_book()
    monkeypatch.setattr(
        ph, "BookService", lambda: StubBookService(reading_books=[book], book_by_id={"1": book})
    )
    handler = ph.ProgressHandler()

    handler.handle(make_context(fake_api, 1, "/progress", storage=storage))
    handler.handle(make_context(fake_api, 1, "1", storage=storage))
    assert storage.get(1)["state"] == "waiting_for_progress_input"

    handler.handle(back_context(fake_api, storage, "/progress"))

    state = storage.get(1)
    assert state["state"] == "selecting_reading_book"
    assert state["data"]["books"] == ["1"]
    assert "Книги в статусе «Читаю»" in fake_api.sent_messages[-1]["message"]


def test_progress_back_from_filter_to_reading_list(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    book = make_book()
    monkeypatch.setattr(
        ph, "BookService", lambda: StubBookService(reading_books=[book], book_by_id={"1": book})
    )
    handler = ph.ProgressHandler()

    handler.handle(make_context(fake_api, 1, "/progress", storage=storage))
    handler.handle(make_context(fake_api, 1, "Другие", storage=storage))
    assert storage.get(1)["state"] == "choose_filter"

    handler.handle(back_context(fake_api, storage, "/progress"))

    state = storage.get(1)
    assert state["state"] == "selecting_reading_book"
    assert state["history"] == []
    assert "Книги в статусе «Читаю»" in fake_api.sent_messages[-1]["message"]
    assert "Назад" not in keyboard_labels(fake_api.sent_messages[-1]["keyboard"])


def test_progress_filter_root_without_reading_has_no_back(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    monkeypatch.setattr(ph, "BookService", lambda: StubBookService(reading_books=[]))
    handler = ph.ProgressHandler()

    handler.handle(make_context(fake_api, 1, "/progress", storage=storage))

    assert storage.get(1)["state"] == "choose_filter"
    assert storage.get(1).get("history", []) == []
    assert "Назад" not in keyboard_labels(fake_api.sent_messages[-1]["keyboard"])

    messages_before = len(fake_api.sent_messages)
    handler.handle(back_context(fake_api, storage, "/progress"))
    assert len(fake_api.sent_messages) == messages_before
    assert storage.get(1)["state"] == "choose_filter"


def test_progress_back_from_confirm_to_input_clears_pending(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    book = make_book()
    seed_state(
        storage,
        "/progress",
        "waiting_for_progress_confirm",
        data={
            "selected_book_id": "1",
            "progress_book_pages": 319,
            "pending_progress_page": 200,
        },
        history=[
            {
                "state": "waiting_for_progress_input",
                "data": {"selected_book_id": "1", "progress_book_pages": 319},
            }
        ],
    )
    monkeypatch.setattr(puf, "BookService", lambda: StubBookService(book_by_id={"1": book}))

    ph.ProgressHandler().handle(back_context(fake_api, storage, "/progress"))

    state = storage.get(1)
    assert state["state"] == "waiting_for_progress_input"
    assert "pending_progress_page" not in state["data"]
    assert "Введи текущую страницу" in fake_api.sent_messages[-1]["message"]


def test_progress_back_from_input_to_shared_book_list_restores_books():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    seed_state(
        storage,
        "/progress",
        "waiting_for_progress_input",
        data={"selected_book_id": "1", "progress_book_pages": 319, "books": ["9"]},
        history=[
            {
                "state": "selecting_book",
                "data": {
                    "books": ["1", "2"],
                    "list_header": "H\n",
                    "book_lines": ["a\n", "b\n"],
                },
            }
        ],
    )

    ph.ProgressHandler().handle(back_context(fake_api, storage, "/progress"))

    state = storage.get(1)
    assert state["state"] == "selecting_book"
    assert state["data"]["books"] == ["1", "2"]
    assert fake_api.sent_messages[-1]["message"] == "H\na\nb\n"


def test_book_selection_render_current_filter_and_status(monkeypatch):
    """Перерисовка flow-owned шагов выбора книги после «Назад»."""
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    seed_state(
        storage,
        "/progress",
        "selecting_status_filter",
        history=[{"state": "choose_filter", "data": {}}],
    )

    ph.ProgressHandler().handle(back_context(fake_api, storage, "/progress"))

    assert storage.get(1)["state"] == "choose_filter"
    assert fake_api.sent_messages[-1]["message"] == "Какие книги интересуют?"


def test_selection_flow_owner_command_used_in_back_payload(monkeypatch):
    """Кнопка «Назад» на flow-шаге несёт команду владельца сценария."""
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    book = make_book()
    monkeypatch.setattr(
        ph, "BookService", lambda: StubBookService(reading_books=[book], book_by_id={"1": book})
    )
    monkeypatch.setattr(bsf, "BookService", lambda: StubBookService(book_by_id={"1": book}))
    handler = ph.ProgressHandler()

    handler.handle(make_context(fake_api, 1, "/progress", storage=storage))
    handler.handle(make_context(fake_api, 1, "Другие", storage=storage))

    keyboard = fake_api.sent_messages[-1]["keyboard"]
    data = json.loads(keyboard) if isinstance(keyboard, str) else keyboard
    payloads = [
        json.loads(button["action"].get("payload") or "{}")
        for row in data["buttons"]
        for button in row
    ]
    assert {"command": "/progress", "action": "back"} in payloads
