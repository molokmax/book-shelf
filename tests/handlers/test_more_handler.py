"""Тесты обработчика навигации «Ещё»/«Назад» и клавиатуры подменю."""

import json
from unittest.mock import MagicMock

from vk_bot.command_router import CommandRouter
from vk_bot.handlers.cancel import CancelHandler
from vk_bot.handlers.more import MoreHandler
from vk_bot.keyboards import more_keyboard


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


def keyboard_labels(keyboard):
    data = keyboard if isinstance(keyboard, dict) else json.loads(keyboard)
    return [button["action"]["label"] for row in data["buttons"] for button in row]


def keyboard_payloads(keyboard):
    """Payload-команды кнопок клавиатуры (None у кнопок без payload)."""
    data = keyboard if isinstance(keyboard, dict) else json.loads(keyboard)
    payloads = []
    for row in data["buttons"]:
        for button in row:
            raw = button["action"].get("payload")
            payloads.append(json.loads(raw) if raw else None)
    return payloads


def test_more_keyboard_layout():
    labels = keyboard_labels(more_keyboard().get_keyboard())
    payloads = keyboard_payloads(more_keyboard().get_keyboard())

    assert labels[:3] == ["/edit", "/export", "/goal"]
    assert labels[3:] == ["/stats", "/settings", "Назад"]
    assert payloads[:5] == [None] * 5
    assert payloads[5] == {"command": "/back"}


def test_more_opens_submenu_without_state():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    ctx = make_context(fake_api, 1, "Ещё", payload={"command": "/more"}, storage=storage)
    result = MoreHandler().handle(ctx)

    assert result is True
    msg = fake_api.sent_messages[-1]
    assert msg["message"].startswith("Ещё")
    assert "/edit" in msg["message"]
    assert "/settings" in msg["message"]
    assert keyboard_labels(msg["keyboard"]) == [
        "/edit",
        "/export",
        "/goal",
        "/stats",
        "/settings",
        "Назад",
    ]
    # Навигация не сценарий: состояние не должно появиться
    assert not storage.is_active(1)
    assert storage.get_command(1) is None


def test_back_returns_to_main_menu():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    ctx = make_context(fake_api, 2, "Назад", payload={"command": "/back"}, storage=storage)
    MoreHandler().handle(ctx)

    msg = fake_api.sent_messages[-1]
    assert msg["message"] == "Главное меню"
    labels = keyboard_labels(msg["keyboard"])
    assert labels[:3] == ["/progress", "/details", "/list"]
    assert "Ещё" in labels
    assert not storage.is_active(2)


def test_more_guard_other_scenario():
    """«Ещё» при чужом активном сценарии не перехватывается."""
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    storage.save(3, {"command": "/add", "state": "waiting_for_title", "data": {}})

    ctx = make_context(fake_api, 3, "Ещё", payload={"command": "/more"}, storage=storage)
    result = MoreHandler().handle(ctx)

    assert result is None
    assert fake_api.sent_messages == []


def test_back_guard_other_scenario():
    """«Назад» при чужом активном сценарии не перехватывается."""
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    storage.save(4, {"command": "/edit", "state": "choose_filter", "data": {}})

    ctx = make_context(fake_api, 4, "Назад", payload={"command": "/back"}, storage=storage)
    result = MoreHandler().handle(ctx)

    assert result is None
    assert fake_api.sent_messages == []


def test_cancel_intercepts_submenu():
    """Набранная «Отмена» перехватывается CancelHandler даже с экрана «Ещё»."""
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    router = CommandRouter()
    router.register_handler(CancelHandler())
    router.register_handler(MoreHandler())

    ctx = make_context(fake_api, 5, "отмена", storage=storage)
    result = router.route(ctx)

    assert result is True
    assert "Операция отменена" in fake_api.sent_messages[-1]["message"]
