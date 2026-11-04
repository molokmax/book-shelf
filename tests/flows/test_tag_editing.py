"""Тесты TagEditingFlow: toggle, ввод, пагинация, подтверждение."""

import json
from unittest.mock import MagicMock

import pytest

from vk_bot.context import BotContext
from vk_bot.flows import tag_editing as tf


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


class FakeVkApiMethod:
    def __init__(self):
        self.sent_messages = []
        self.messages = self

    def send(self, **kwargs):
        self.sent_messages.append(kwargs)


@pytest.fixture
def api():
    return FakeVkApiMethod()


@pytest.fixture
def stub_dictionary(monkeypatch):
    """Справочник тегов пользователя, изменяемый по тестовой потребности."""
    tags = {"list": ["Classic", "Fantasy"]}

    class StubTagService:
        def get_user_tags(self, user_id):
            return list(tags["list"])

    monkeypatch.setattr(tf, "TagService", StubTagService)
    return tags


def make_context(user_id, api, text="", payload=None, storage=None):
    vk = MagicMock()
    vk.get_api.return_value = api
    event = MagicMock()
    event.user_id = user_id
    event.peer_id = user_id
    event.text = text
    event.payload = json.dumps(payload) if payload else None
    context = BotContext(
        vk=vk, upload=MagicMock(), event=event, storage=storage or FakeStateStorage()
    )
    return context


def make_flow():
    done: list[list[str]] = []
    flow = tf.TagEditingFlow("/add", lambda context, selection: done.append(selection))
    return flow, done


def seed_state(user_id, data=None):
    storage = FakeStateStorage()
    storage.save(
        user_id,
        {
            "command": "/add",
            "state": "selecting_tags",
            "data": data if data is not None else {},
        },
    )
    return storage


def keyboard_labels(keyboard) -> list[str]:
    data = keyboard if isinstance(keyboard, dict) else json.loads(keyboard)
    return [button["action"]["label"] for row in data["buttons"] for button in row]


def test_start_keeps_preselected_tags(api, stub_dictionary):
    flow, done = make_flow()
    storage = seed_state(1, data={"title": "T"})
    context = make_context(1, api, storage=storage)

    flow.start(context, storage.get(1), preselected=["Old"])

    state = storage.get(1)
    assert state["state"] == "selecting_tags"
    assert state["data"]["selected_tags"] == ["Old"]
    assert "Выбрано: Old" in api.sent_messages[-1]["message"]
    assert "Готово" in keyboard_labels(api.sent_messages[-1]["keyboard"])
    assert done == []


def test_toggle_adds_then_removes_tag(api, stub_dictionary):
    flow, _ = make_flow()
    storage = seed_state(2)
    context = make_context(2, api, storage=storage)
    flow.start(context, storage.get(2))

    toggle = make_context(
        2, api, payload={"command": "/add", "action": "toggle", "tag": "Fantasy"}, storage=storage
    )
    flow.handle(toggle)

    assert "Выбрано: Fantasy" in api.sent_messages[-1]["message"]
    assert storage.get(2)["data"]["selected_tags"] == ["Fantasy"]

    flow.handle(toggle)

    assert "Выбрано: нет" in api.sent_messages[-1]["message"]
    assert storage.get(2)["data"]["selected_tags"] == []


def test_toggle_ignores_unknown_tag(api, stub_dictionary):
    flow, _ = make_flow()
    storage = seed_state(3)
    context = make_context(3, api, storage=storage)
    flow.start(context, storage.get(3))

    spoofed = make_context(
        3,
        api,
        payload={"command": "/add", "action": "toggle", "tag": "Не существует"},
        storage=storage,
    )
    flow.handle(spoofed)

    assert "Не удалось обработать сообщение" in api.sent_messages[-1]["message"]
    assert storage.get(3)["data"]["selected_tags"] == []


def test_typed_list_adds_with_casefold_resolve(api, stub_dictionary):
    flow, _ = make_flow()
    storage = seed_state(4)
    context = make_context(4, api, storage=storage)
    flow.start(context, storage.get(4))

    typed = make_context(4, api, text="CLASSIC, academic", storage=storage)
    flow.handle(typed)

    # casefold резолвится к канонической форме из справочника
    assert storage.get(4)["data"]["selected_tags"] == ["Classic", "academic"]
    assert "Выбрано: academic, Classic" in api.sent_messages[-1]["message"]


def test_empty_typed_input_shows_invalid(api, stub_dictionary):
    flow, _ = make_flow()
    storage = seed_state(5)
    context = make_context(5, api, storage=storage)
    flow.start(context, storage.get(5))

    empty = make_context(5, api, text=" ,  ", storage=storage)
    flow.handle(empty)

    assert "Не удалось обработать сообщение" in api.sent_messages[-1]["message"]
    assert "Введи теги через запятую" in api.sent_messages[-1]["message"]
    assert storage.get(5)["state"] == "selecting_tags"


def test_typed_done_confirms_flow(api, stub_dictionary):
    flow, done = make_flow()
    storage = seed_state(6, data={"selected_tags": ["Fantasy"], "user_id": "u-6"})
    storage.get(6)["state"] = "selecting_tags"
    context = make_context(6, api, text="готово", storage=storage)

    flow.handle(context)

    assert done == [["Fantasy"]]


def test_done_payload_confirms_sorted_selection(api, stub_dictionary):
    flow, done = make_flow()
    storage = seed_state(7, data={"selected_tags": ["b", "a"], "user_id": "u-7"})
    context = make_context(7, api, payload={"command": "/add", "action": "done"}, storage=storage)

    flow.handle(context)

    assert done == [["a", "b"]]


def test_pagination_navigates_pages(api, stub_dictionary):
    stub_dictionary["list"] = [f"tag-{index:02d}" for index in range(20)]
    flow, _ = make_flow()
    storage = seed_state(8)
    context = make_context(8, api, storage=storage)
    flow.start(context, storage.get(8))

    page = make_context(8, api, payload={"command": "/add", "action": "next_page"}, storage=storage)
    flow.handle(page)

    labels = keyboard_labels(api.sent_messages[-1]["keyboard"])
    assert "tag-16" in labels
    assert "tag-15" not in labels
    assert "← Назад" in labels
    assert "Ещё →" not in labels
    assert storage.get(8)["data"]["tag_page"] == 1

    back = make_context(8, api, payload={"command": "/add", "action": "prev_page"}, storage=storage)
    flow.handle(back)

    labels = keyboard_labels(api.sent_messages[-1]["keyboard"])
    assert "tag-15" in labels
    assert "Ещё →" in labels
    assert storage.get(8)["data"]["tag_page"] == 0


def test_tag_named_like_service_buttons_routes_by_payload(api, stub_dictionary):
    # Имена тегов не конфликтуют с кнопками «Готово»/«Отмена»: различие через payload
    stub_dictionary["list"] = ["Готово", "Отмена", "/add"]
    flow, _ = make_flow()
    storage = seed_state(9)
    context = make_context(9, api, storage=storage)
    flow.start(context, storage.get(9))

    toggle = make_context(
        9, api, payload={"command": "/add", "action": "toggle", "tag": "Отмена"}, storage=storage
    )
    flow.handle(toggle)

    assert storage.get(9)["data"]["selected_tags"] == ["Отмена"]
