"""Тесты одношаговой команды /achievements."""

from datetime import datetime

import pytest
from conftest import FakeStateStorage
from conftest import FakeVkApi as FakeVkApiMethod
from conftest import make_context

from core.models import ACHIEVEMENT_DEFINITIONS, AchievementCheckResult, AchievementStatus
from vk_bot.handlers import achievements as ah

NOW = datetime(2026, 11, 24, 12, 30)


class AchievementServiceStub:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.checked_user_id = None

    def check(self, user_id):
        self.checked_user_id = user_id
        if self.error:
            raise self.error
        return self.result


@pytest.fixture(autouse=True)
def patch_user(monkeypatch):
    monkeypatch.setattr(
        ah,
        "get_or_create_user",
        lambda api, user_id: type("User", (), {"id": f"internal-{user_id}"})(),
    )


def make_result(with_new=False):
    statuses = [
        AchievementStatus(
            definition=definition,
            current=1 if definition.key == "books_1" else 0,
            unlocked_at=NOW if definition.key == "books_1" else None,
        )
        for definition in ACHIEVEMENT_DEFINITIONS
    ]
    return AchievementCheckResult(
        statuses=statuses,
        new_achievements=[ACHIEVEMENT_DEFINITIONS[0]] if with_new else [],
    )


def test_catalog_unlocks_retrospective_achievements_without_state(monkeypatch):
    service = AchievementServiceStub(make_result(with_new=True))
    monkeypatch.setattr(ah, "AchievementService", lambda: service)
    api = FakeVkApiMethod()
    storage = FakeStateStorage()

    result = ah.AchievementsHandler().handle(
        make_context(api, 42, "/achievements", storage=storage)
    )

    assert result is True
    assert service.checked_user_id == "internal-42"
    assert len(api.sent_messages) == 1
    message = api.sent_messages[0]["message"]
    assert message.startswith("🏆 Новое достижение: «Первая книга»!\n\n🏆 Достижения")
    assert "Получено: 2026-11-24" in message
    assert storage.get(42) == {}


def test_catalog_without_new_achievements_has_no_congratulation(monkeypatch):
    monkeypatch.setattr(ah, "AchievementService", lambda: AchievementServiceStub(make_result()))
    api = FakeVkApiMethod()

    ah.AchievementsHandler().handle(make_context(api, 1, "/achievements"))

    message = api.sent_messages[-1]["message"]
    assert message.startswith("🏆 Достижения")
    assert "Новое достижение" not in message


def test_catalog_service_error_is_managed(monkeypatch, caplog):
    service = AchievementServiceStub(error=RuntimeError("database unavailable"))
    monkeypatch.setattr(ah, "AchievementService", lambda: service)
    api = FakeVkApiMethod()

    result = ah.AchievementsHandler().handle(make_context(api, 1, "/achievements"))

    assert result is True
    assert api.sent_messages[-1]["message"] == (
        "⚠️ Не удалось обработать сообщение. Попробуй открыть каталог ещё раз позже."
    )
    assert "database unavailable" in caplog.text
