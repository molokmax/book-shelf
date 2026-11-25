"""Тесты пользовательского форматирования достижений."""

from datetime import datetime

from core.models import ACHIEVEMENT_DEFINITIONS, AchievementStatus
from utils.helpers import format_achievement_catalog, format_new_achievements

NOW = datetime(2026, 11, 24, 12, 30)


def test_format_new_achievements_empty():
    assert format_new_achievements([]) is None


def test_format_new_achievements_single():
    result = format_new_achievements([ACHIEVEMENT_DEFINITIONS[0]])

    assert result == "🏆 Новое достижение: «Первая книга»!"


def test_format_new_achievements_multiple_in_catalog_order():
    result = format_new_achievements([ACHIEVEMENT_DEFINITIONS[0], ACHIEVEMENT_DEFINITIONS[2]])

    assert result == "🏆 Новые достижения!\n• Первая книга\n• Первый финиш"


def test_format_achievement_catalog_shows_dates_progress_and_fixed_order():
    statuses = [
        AchievementStatus(
            definition=definition,
            current=4 if definition.metric.value == "books" else 0,
            unlocked_at=NOW if definition.key == "books_1" else None,
        )
        for definition in ACHIEVEMENT_DEFINITIONS
    ]

    result = format_achievement_catalog(statuses)

    assert result.startswith("🏆 Достижения\n\n✅ Первая книга")
    assert "Добавь 1 книгу в библиотеку.\nПолучено: 2026-11-24" in result
    assert "🔒 Своя библиотека\nСобери библиотеку из 10 книг.\nПрогресс: 4/10" in result
    positions = [result.index(definition.title) for definition in ACHIEVEMENT_DEFINITIONS]
    assert positions == sorted(positions)
