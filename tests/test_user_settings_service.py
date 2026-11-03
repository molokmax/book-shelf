"""Тесты сервиса персональных настроек пользователя (уровень БД)."""

import uuid

import pytest

from core.database import Database
from core.db import get_db
from core.models import User
from core.services import UserSettingsService


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


def test_default_period_without_row(service, db_path):
    user_id = create_user(db_path)
    assert service.get_reading_speed_period(user_id) == 30


def test_set_period_creates_single_row(service, db_path):
    user_id = create_user(db_path)

    service.set_reading_speed_period(user_id, 14)

    assert service.get_reading_speed_period(user_id) == 14
    db = get_db(db_path)
    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM user_settings WHERE user_id = ?", (user_id,))
        assert cur.fetchone()[0] == 1


def test_set_period_updates_existing_row(service, db_path):
    user_id = create_user(db_path)
    service.set_reading_speed_period(user_id, 14)
    db = get_db(db_path)
    with db.get_cursor() as cur:
        cur.execute("SELECT created_at FROM user_settings WHERE user_id = ?", (user_id,))
        created_at_before = cur.fetchone()[0]

    service.set_reading_speed_period(user_id, 7)

    assert service.get_reading_speed_period(user_id) == 7
    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM user_settings WHERE user_id = ?", (user_id,))
        assert cur.fetchone()[0] == 1
        cur.execute(
            "SELECT created_at, updated_at FROM user_settings WHERE user_id = ?",
            (user_id,),
        )
        created_at, updated_at = cur.fetchone()
        # created_at не перезаписывается, updated_at двигается при обновлении
        assert created_at == created_at_before
        assert updated_at >= created_at


def test_set_invalid_period_raises(service, db_path):
    user_id = create_user(db_path)

    with pytest.raises(ValueError):
        service.set_reading_speed_period(user_id, 21)

    # Некорректное значение не сохраняется
    assert service.get_reading_speed_period(user_id) == 30


def test_set_period_for_unknown_user_fails(service, db_path):
    # Внешний ключ требует существующего пользователя
    with pytest.raises(Exception):
        service.set_reading_speed_period("unknown-user-id", 7)


def test_user_settings_table_is_idempotent(db_path):
    """Повторная инициализация базы не падает и не сбрасывает настройки."""
    svc = UserSettingsService(db_path=db_path)
    user_id = create_user(db_path)
    svc.set_reading_speed_period(user_id, 14)

    # Повторное открытие базы создаёт таблицы заново (IF NOT EXISTS)
    Database(db_path)

    assert svc.get_reading_speed_period(user_id) == 14
