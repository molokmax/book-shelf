"""Тесты обработчика команды /goal."""

import json
import types

import pytest
from conftest import FakeStateStorage
from conftest import FakeVkApi as FakeVkApiMethod
from conftest import make_context

from vk_bot.handlers import goal as gh
from vk_bot.handlers.base import FOREIGN_SCENARIO_MESSAGE


class FakeUser:
    def __init__(self, user_id="user-1"):
        self.id = user_id


class GoalStub:
    def __init__(self, target=None, pages_today=0):
        self.target = target
        self.pages_today = pages_today
        self.saved = None
        self.disabled = False
        self._goal = types.SimpleNamespace(target=target) if target is not None else None

    def get_goal(self, user_id):
        return self._goal

    def get_goal_status(self, user_id):
        if self._goal is None:
            return None
        percent = min(100, round(self.pages_today / self.target * 100))
        return types.SimpleNamespace(
            goal=self._goal,
            pages_today=self.pages_today,
            percent=percent,
            completed=self.pages_today >= self.target,
            remaining=max(0, self.target - self.pages_today),
        )

    def set_daily_goal(self, user_id, target):
        self.saved = (user_id, target)
        self._goal = types.SimpleNamespace(target=target)
        return self._goal

    def disable_goal(self, user_id):
        self.disabled = True
        existed = self._goal is not None
        self._goal = None
        return existed


def keyboard_labels(keyboard):
    data = keyboard if isinstance(keyboard, dict) else json.loads(keyboard)
    return [button["action"]["label"] for row in data["buttons"] for button in row]


def save_state(storage, user_id, state="menu", **data):
    storage.save(
        user_id,
        {"command": "/goal", "state": state, "data": {"user_id": "user-1", **data}},
    )


@pytest.fixture(autouse=True)
def patch_user(monkeypatch):
    monkeypatch.setattr(gh, "get_or_create_user", lambda api, user_id: FakeUser())


def test_entry_shows_goal_with_progress(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    monkeypatch.setattr(gh, "GoalService", lambda: GoalStub(target=50, pages_today=35))

    ctx = make_context(fake_api, 2, "/goal", storage=storage)
    gh.GoalHandler().handle(ctx)

    assert len(fake_api.sent_messages) == 1
    msg = fake_api.sent_messages[-1]
    assert msg["message"] == (
        "Цель на день: 50 стр.\n"
        "Сегодня прочитано: 35 стр. (70%)\n"
        "Осталось: 15 стр.\n\n"
        "Выбери действие:"
    )
    assert keyboard_labels(msg["keyboard"]) == ["Установить", "Отключить", "Отмена"]
    assert storage.get(2)["state"] == "menu"


def test_entry_shows_completed_goal(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    monkeypatch.setattr(gh, "GoalService", lambda: GoalStub(target=50, pages_today=60))

    ctx = make_context(fake_api, 3, "/goal", storage=storage)
    gh.GoalHandler().handle(ctx)

    assert len(fake_api.sent_messages) == 1
    msg = fake_api.sent_messages[-1]
    assert msg["message"] == (
        "Цель на день: 50 стр.\n"
        "Сегодня прочитано: 60 стр. (100%)\n"
        "Цель выполнена.\n\n"
        "Выбери действие:"
    )
    assert keyboard_labels(msg["keyboard"]) == ["Установить", "Отключить", "Отмена"]
    assert storage.get(3)["state"] == "menu"


def test_entry_without_goal_shows_hint(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    monkeypatch.setattr(gh, "GoalService", lambda: GoalStub())

    ctx = make_context(fake_api, 4, "/goal", storage=storage)
    gh.GoalHandler().handle(ctx)

    assert len(fake_api.sent_messages) == 1
    msg = fake_api.sent_messages[-1]
    assert msg["message"] == (
        "Цель на день\n\n"
        "Цель на день не установлена.\n\n"
        "Нажми «Установить», чтобы задать количество страниц в день."
    )
    assert keyboard_labels(msg["keyboard"]) == ["Установить", "Отключить", "Отмена"]
    assert storage.get(4)["state"] == "menu"


def test_set_action_requests_value(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 5)
    monkeypatch.setattr(gh, "GoalService", lambda: GoalStub())

    ctx = make_context(fake_api, 5, "Установить", storage=storage)
    gh.GoalHandler().handle(ctx)

    msg = fake_api.sent_messages[-1]
    assert "Введи количество страниц в день" in msg["message"]
    assert keyboard_labels(msg["keyboard"]) == ["Отмена", "Назад"]
    assert storage.get(5)["state"] == "waiting_for_goal_input"


def test_set_valid_value(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 6, state="waiting_for_goal_input")
    stub = GoalStub()
    monkeypatch.setattr(gh, "GoalService", lambda: stub)

    ctx = make_context(fake_api, 6, "25", storage=storage)
    gh.GoalHandler().handle(ctx)

    assert stub.saved == ("user-1", 25)
    assert fake_api.sent_messages[-1]["message"] == "Цель на день установлена: 25 стр."
    assert not storage.is_active(6)


def test_set_zero_disables_goal(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 7, state="waiting_for_goal_input")
    stub = GoalStub(target=50)
    monkeypatch.setattr(gh, "GoalService", lambda: stub)

    ctx = make_context(fake_api, 7, "0", storage=storage)
    gh.GoalHandler().handle(ctx)

    assert stub.disabled is True
    assert fake_api.sent_messages[-1]["message"] == "Цель отключена."
    assert not storage.is_active(7)


@pytest.mark.parametrize("value", ["abc", "-5", "2.5"])
def test_set_invalid_value_keeps_state(monkeypatch, value):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 8, state="waiting_for_goal_input")
    stub = GoalStub()
    monkeypatch.setattr(gh, "GoalService", lambda: stub)

    ctx = make_context(fake_api, 8, value, storage=storage)
    gh.GoalHandler().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert msg.startswith("⚠️ Не удалось обработать сообщение.")
    assert stub.saved is None
    assert storage.get(8)["state"] == "waiting_for_goal_input"


def test_disable_existing_goal(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 9)
    stub = GoalStub(target=50)
    monkeypatch.setattr(gh, "GoalService", lambda: stub)

    ctx = make_context(fake_api, 9, "Отключить", storage=storage)
    gh.GoalHandler().handle(ctx)

    assert stub.disabled is True
    assert fake_api.sent_messages[-1]["message"] == "Цель отключена."
    assert not storage.is_active(9)


def test_disable_without_goal(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 10)
    stub = GoalStub()
    monkeypatch.setattr(gh, "GoalService", lambda: stub)

    ctx = make_context(fake_api, 10, "Отключить", storage=storage)
    gh.GoalHandler().handle(ctx)

    assert fake_api.sent_messages[-1]["message"] == "Цель не установлена."
    assert not storage.is_active(10)


@pytest.mark.parametrize("value", ["непонятно", "Просмотр"])
def test_invalid_menu_choice_keeps_menu(monkeypatch, value):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 11)
    monkeypatch.setattr(gh, "GoalService", lambda: GoalStub())

    ctx = make_context(fake_api, 11, value, storage=storage)
    gh.GoalHandler().handle(ctx)

    msg = fake_api.sent_messages[-1]
    assert msg["message"] == "⚠️ Не удалось обработать сообщение. Выбери действие из клавиатуры."
    assert keyboard_labels(msg["keyboard"]) == ["Установить", "Отключить", "Отмена"]
    assert storage.get(11)["state"] == "menu"


def test_handler_declines_other_active_state():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    storage.save(12, {"command": "/add", "state": "waiting_for_title", "data": {}})

    ctx = make_context(fake_api, 12, "/goal", storage=storage)
    result = gh.GoalHandler().handle(ctx)

    assert result is True
    assert fake_api.sent_messages[-1]["message"] == FOREIGN_SCENARIO_MESSAGE
    assert storage.get(12)["state"] == "waiting_for_title"
