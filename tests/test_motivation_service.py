"""Тесты мотивационных фраз: репозиторий и сервисы (уровень БД)."""

import uuid

import pytest

from core.database import Database
from core.db import get_db
from core.migrations import MOTIVATIONAL_SEED_PHRASES
from core.models import MotivationContext, User
from core.repository import MotivationPhraseRepository, UserSettingsRepository
from core.services import MotivationService, UserSettingsService


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def service(db_path):
    return UserSettingsService(db_path=db_path)


def create_user(db_path) -> str:
    """Создаёт пользователя в БД (нужен для внешнего ключа)."""
    db = get_db(db_path)
    user = User(id=str(uuid.uuid4()), external_id=uuid.uuid4().int & 0x7FFFFFFF)
    with db.get_cursor() as cur:
        cur.execute(
            "INSERT INTO users "
            "(id, external_id, username, first_name, last_name, created_at, last_active) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user.id,
                user.external_id,
                user.username,
                user.first_name,
                user.last_name,
                user.created_at.isoformat(),
                user.last_active.isoformat(),
            ),
        )
    return user.id


def make_context(**overrides) -> MotivationContext:
    """Контекст обновления прогресса с осмысленными значениями по умолчанию."""
    defaults = {
        "previous_page": 10,
        "new_page": 30,
        "pages_delta": 20,
        "finished": False,
        "goal_completed": False,
    }
    return MotivationContext(**{**defaults, **overrides})


def test_pick_phrase_returns_from_seeded_list(db_path):
    service = MotivationService(db_path=db_path)

    first = service.pick_phrase(make_context())
    second = service.pick_phrase(make_context())

    assert first in MOTIVATIONAL_SEED_PHRASES
    assert second in MOTIVATIONAL_SEED_PHRASES


def test_pick_phrase_on_empty_table_returns_none(db_path):
    # Один синглтон-коннект на путь: пересоздание заново запустило бы сид
    db = get_db(db_path)
    with db.get_cursor() as cur:
        cur.execute("DELETE FROM motivational_phrases")

    repo = MotivationPhraseRepository(get_db(db_path))

    assert repo.get_random_phrase() is None
    assert MotivationService(db_path=db_path).pick_phrase(make_context()) is None


def test_settings_default_motivation_enabled(service, db_path):
    user_id = create_user(db_path)

    assert service.is_motivation_enabled(user_id) is True


def test_set_motivation_creates_single_row(db_path):
    repo = UserSettingsRepository(get_db(db_path))
    user_id = create_user(db_path)

    repo.set_motivation_enabled(user_id, False)
    repo.set_motivation_enabled(user_id, True)

    db = get_db(db_path)
    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM user_settings WHERE user_id = ?", (user_id,))
        assert cur.fetchone()[0] == 1
    assert repo.get_motivation_enabled(user_id) is True


def test_toggle_motivation_persists_period(db_path):
    repo = UserSettingsRepository(get_db(db_path))
    user_id = create_user(db_path)

    repo.set_motivation_enabled(user_id, False)

    assert repo.get_motivation_enabled(user_id) is False
    # Тоггл создаёт строку с дефолтным периодом и сам период не трогает
    assert repo.get_reading_speed_period(user_id) == 30


def test_set_period_keeps_motivation_value(db_path):
    repo = UserSettingsRepository(get_db(db_path))
    user_id = create_user(db_path)

    repo.set_motivation_enabled(user_id, False)
    repo.set_reading_speed_period(user_id, 14)

    assert repo.get_reading_speed_period(user_id) == 14
    assert repo.get_motivation_enabled(user_id) is False


def test_service_toggle_roundtrip(db_path):
    service = UserSettingsService(db_path=db_path)
    user_id = create_user(db_path)

    service.set_motivation_enabled(user_id, False)
    assert service.is_motivation_enabled(user_id) is False

    service.set_motivation_enabled(user_id, True)
    assert service.is_motivation_enabled(user_id) is True
