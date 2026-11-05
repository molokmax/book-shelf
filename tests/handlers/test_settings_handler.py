"""Тесты обработчика команды /settings."""

import json
import types
from unittest.mock import MagicMock

import pytest

from vk_bot.command_router import CommandRouter
from vk_bot.handlers import settings as sh
from vk_bot.handlers.cancel import CancelHandler


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
    def __init__(self, user_id="user-1"):
        self.id = user_id


class SettingsStub:
    """Дубль сервиса настроек: хранит значения в памяти."""

    def __init__(self, period=30, motivation=True):
        self.period = period
        self.saved = None
        self.motivation = motivation
        self.motivation_saved = None

    def get_reading_speed_period(self, user_id):
        return self.saved if self.saved is not None else self.period

    def set_reading_speed_period(self, user_id, days):
        self.saved = days

    def is_motivation_enabled(self, user_id):
        return self.motivation_saved if self.motivation_saved is not None else self.motivation

    def set_motivation_enabled(self, user_id, enabled):
        self.motivation_saved = enabled


def keyboard_labels(keyboard):
    data = keyboard if isinstance(keyboard, dict) else json.loads(keyboard)
    return [button["action"]["label"] for row in data["buttons"] for button in row]


def keyboard_colors(keyboard):
    data = keyboard if isinstance(keyboard, dict) else json.loads(keyboard)
    return {button["action"]["label"]: button["color"] for row in data["buttons"] for button in row}


def save_state(storage, user_id, command="/settings", state="menu", **data):
    storage.save(
        user_id,
        {"command": command, "state": state, "data": {"user_id": "user-1", **data}},
    )


@pytest.fixture(autouse=True)
def patch_user(monkeypatch):
    monkeypatch.setattr(sh, "get_or_create_user", lambda api, user_id: FakeUser())


def test_entry_shows_screen_and_state(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    monkeypatch.setattr(sh, "UserSettingsService", lambda: SettingsStub())

    ctx = make_context(fake_api, 1, "/settings", storage=storage)
    sh.SettingsHandler().handle(ctx)

    msg = fake_api.sent_messages[-1]
    assert "Настройки" in msg["message"]
    assert "Период скорости чтения: 30 дней" in msg["message"]
    assert "Мотивация: включена" in msg["message"]
    labels = keyboard_labels(msg["keyboard"])
    assert labels == ["7 дней", "14 дней", "30 дней", "Мотивация: Вкл", "Назад"]
    colors = keyboard_colors(msg["keyboard"])
    assert colors["Мотивация: Вкл"] == "primary"
    assert storage.get(1)["state"] == "menu"
    assert storage.get(1)["command"] == "/settings"


def test_entry_shows_saved_period(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    monkeypatch.setattr(sh, "UserSettingsService", lambda: SettingsStub(period=14))

    ctx = make_context(fake_api, 2, "/settings", storage=storage)
    sh.SettingsHandler().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "Период скорости чтения: 14 дней" in msg


def test_entry_shows_motivation_off(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    monkeypatch.setattr(sh, "UserSettingsService", lambda: SettingsStub(motivation=False))

    ctx = make_context(fake_api, 2, "/settings", storage=storage)
    sh.SettingsHandler().handle(ctx)

    msg = fake_api.sent_messages[-1]
    assert "Мотивация: выключена" in msg["message"]
    labels = keyboard_labels(msg["keyboard"])
    assert labels[3] == "Мотивация: Выкл"
    assert keyboard_colors(msg["keyboard"])["Мотивация: Выкл"] == "secondary"


def test_select_period(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 3)
    stub = SettingsStub()
    monkeypatch.setattr(sh, "UserSettingsService", lambda: stub)

    ctx = make_context(fake_api, 3, "14 дней", storage=storage)
    sh.SettingsHandler().handle(ctx)

    assert stub.saved == 14
    msg = fake_api.sent_messages[-1]
    assert "Период скорости чтения: 14 дней" in msg["message"]
    assert keyboard_labels(msg["keyboard"]) == [
        "7 дней",
        "14 дней",
        "30 дней",
        "Мотивация: Вкл",
        "Назад",
    ]
    # Сценарий остаётся активен: можно поменять значение ещё раз
    assert storage.is_active(3)
    assert storage.get(3)["state"] == "menu"


def test_reselect_period_stays_in_menu(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 4)
    stub = SettingsStub()
    monkeypatch.setattr(sh, "UserSettingsService", lambda: stub)

    ctx1 = make_context(fake_api, 4, "14 дней", storage=storage)
    sh.SettingsHandler().handle(ctx1)
    ctx2 = make_context(fake_api, 4, "7 дней", storage=storage)
    sh.SettingsHandler().handle(ctx2)

    assert stub.saved == 7
    msg = fake_api.sent_messages[-1]["message"]
    assert "Период скорости чтения: 7 дней" in msg
    assert storage.is_active(4)


def test_back_returns_to_main_menu(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 5)
    monkeypatch.setattr(sh, "UserSettingsService", lambda: SettingsStub())

    ctx = make_context(fake_api, 5, "Назад", storage=storage)
    sh.SettingsHandler().handle(ctx)

    msg = fake_api.sent_messages[-1]
    assert msg["message"] == "Возврат в главное меню"
    labels = keyboard_labels(msg["keyboard"])
    assert labels[:3] == ["/progress", "/details", "/list"]
    assert "Ещё" in labels
    assert not storage.is_active(5)


def test_invalid_input_stays_in_menu(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 6)
    monkeypatch.setattr(sh, "UserSettingsService", lambda: SettingsStub())

    ctx = make_context(fake_api, 6, "привет", storage=storage)
    sh.SettingsHandler().handle(ctx)

    msg = fake_api.sent_messages[-1]
    assert "Выбери значение из клавиатуры" in msg["message"]
    assert keyboard_labels(msg["keyboard"]) == [
        "7 дней",
        "14 дней",
        "30 дней",
        "Мотивация: Вкл",
        "Назад",
    ]
    assert storage.is_active(6)


def test_guard_other_scenario(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 7, command="/edit", state="selecting_book")
    monkeypatch.setattr(sh, "UserSettingsService", lambda: SettingsStub())

    ctx = make_context(fake_api, 7, "/settings", storage=storage)
    result = sh.SettingsHandler().handle(ctx)

    assert result is None
    assert fake_api.sent_messages == []


def test_cancel_intercepts_settings_scenario(monkeypatch):
    """Набранная «Отмена» перехватывается CancelHandler даже в настройках."""
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 8)

    router = CommandRouter()
    router.register_handler(CancelHandler())
    router.register_handler(sh.SettingsHandler())
    monkeypatch.setattr(sh, "UserSettingsService", lambda: SettingsStub())

    ctx = make_context(fake_api, 8, "отмена", storage=storage)
    result = router.route(ctx)

    assert result is True
    assert "Операция отменена" in fake_api.sent_messages[-1]["message"]
    assert not storage.is_active(8)


# ── Тоггл мотивации ───────────────────────────────────────────────────────────


def test_toggle_motivation_disables(monkeypatch):
    """Тап по кнопке «Мотивация: Вкл» выключает мотивацию."""
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 9)
    stub = SettingsStub(motivation=True)
    monkeypatch.setattr(sh, "UserSettingsService", lambda: stub)

    ctx = make_context(fake_api, 9, "Мотивация: Вкл", storage=storage)
    sh.SettingsHandler().handle(ctx)

    assert stub.motivation_saved is False
    msg = fake_api.sent_messages[-1]
    assert msg["message"] == "Мотивация выключена"
    labels = keyboard_labels(msg["keyboard"])
    assert labels == ["7 дней", "14 дней", "30 дней", "Мотивация: Выкл", "Назад"]
    assert keyboard_colors(msg["keyboard"])["Мотивация: Выкл"] == "secondary"
    # Сценарий остаётся активен
    assert storage.is_active(9)
    assert storage.get(9)["state"] == "menu"


def test_toggle_motivation_enables(monkeypatch):
    """Тап по кнопке «Мотивация: Выкл» включает мотивацию."""
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 10)
    stub = SettingsStub(motivation=False)
    monkeypatch.setattr(sh, "UserSettingsService", lambda: stub)

    ctx = make_context(fake_api, 10, "Мотивация: Выкл", storage=storage)
    sh.SettingsHandler().handle(ctx)

    assert stub.motivation_saved is True
    msg = fake_api.sent_messages[-1]
    assert msg["message"] == "Мотивация включена"
    labels = keyboard_labels(msg["keyboard"])
    assert labels[3] == "Мотивация: Вкл"
    assert keyboard_colors(msg["keyboard"])["Мотивация: Вкл"] == "primary"
    assert storage.is_active(10)


def test_double_toggle_returns_to_initial_state(monkeypatch):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 11)
    stub = SettingsStub(motivation=True)
    monkeypatch.setattr(sh, "UserSettingsService", lambda: stub)

    ctx1 = make_context(fake_api, 11, "Мотивация: Вкл", storage=storage)
    sh.SettingsHandler().handle(ctx1)
    ctx2 = make_context(fake_api, 11, "Мотивация: Выкл", storage=storage)
    sh.SettingsHandler().handle(ctx2)

    assert stub.motivation_saved is True
    assert fake_api.sent_messages[-1]["message"] == "Мотивация включена"


def test_period_selection_keeps_motivation_state(monkeypatch):
    """Выбор периода не трогает мотивацию и клавиатура показывает её состояние."""
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    save_state(storage, 12)
    stub = SettingsStub(motivation=False)
    monkeypatch.setattr(sh, "UserSettingsService", lambda: stub)

    ctx = make_context(fake_api, 12, "14 дней", storage=storage)
    sh.SettingsHandler().handle(ctx)

    assert stub.motivation_saved is None
    labels = keyboard_labels(fake_api.sent_messages[-1]["keyboard"])
    assert labels == ["7 дней", "14 дней", "30 дней", "Мотивация: Выкл", "Назад"]
