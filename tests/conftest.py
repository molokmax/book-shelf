import os
import tempfile
import types

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
