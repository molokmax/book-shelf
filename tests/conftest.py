import json
import os
import tempfile
import types
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="book-shelf-tests-"))


@pytest.fixture(autouse=True)
def fake_user_service(monkeypatch):
    """Не создаём пользователей через VK API в тестах handler-ов."""

    class FakeUserService:
        def get_or_create_user(self, external_id, factory):
            return types.SimpleNamespace(id=f"user-{external_id}")

    monkeypatch.setattr("vk_bot.user_helpers.UserService", lambda: FakeUserService())


class FakeVkApi:
    """Заглушка vk_api: возвращает message_id из send и фиксирует удаления.

    Имитирует поведение реального API для механизма цепочки промежуточных
    сообщений (issue #44): send возвращает id отправленного сообщения,
    delete запоминает удалённые id.
    """

    def __init__(self):
        self.sent_messages = []
        self.deleted_ids = []
        self._next_message_id = 1
        # self выступает пространством messages: api.messages.send(...)
        self.messages = self

    def send(self, **kwargs):
        self.sent_messages.append(kwargs)
        message_id = self._next_message_id
        self._next_message_id += 1
        return {"message_id": message_id}

    def delete(self, message_ids=None, delete_for_all=0, **kwargs):
        ids = message_ids or []
        self.deleted_ids.extend(ids)
        return len(ids)


class FakeStateStorage:
    """In-memory заглушка ActiveStateStorage."""

    def __init__(self):
        self._data = {}

    def get(self, user_id):
        import copy

        return copy.deepcopy(self._data.get(user_id, {}))

    def save(self, user_id, state):
        import copy

        self._data[user_id] = copy.deepcopy(state)

    def delete(self, user_id):
        self._data.pop(user_id, None)

    def is_active(self, user_id):
        return bool(self._data.get(user_id))

    def get_command(self, user_id):
        state = self._data.get(user_id)
        return state.get("command") if state else None

    def get_current_state(self, user_id):
        state = self._data.get(user_id)
        return state.get("state") if state else None


def make_context(api, user_id, text="", payload=None, storage=None):
    """Собирает BotContext поверх фейкового API и хранилища стейта."""
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
