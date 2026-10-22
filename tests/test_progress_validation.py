import pytest

from core.progress_validation import (
    BOOK_SHARE_THRESHOLD,
    MIN_JUMP_PAGES,
    SPEED_MULTIPLIER,
    SuspicionReason,
    classify_progress_update,
)


def test_rollback_always_requires_confirmation():
    reasons = classify_progress_update(
        previous_page=55, new_page=54, pages=319, avg_pages_per_day=2.89
    )

    assert len(reasons) == 1
    assert reasons[0].reason == SuspicionReason.ROLLBACK
    assert reasons[0].delta == -1


def test_same_value_is_not_suspicious():
    assert classify_progress_update(55, 55, 319, 2.89) == []


def test_small_forward_step_is_not_suspicious():
    # 7 * 2.89 = 20.23, дельта 20 меньше порога
    assert classify_progress_update(55, 75, 319, 2.89) == []


def test_jump_by_speed_has_reason():
    reasons = classify_progress_update(55, 300, 319, 2.89)

    assert len(reasons) == 1
    reason = reasons[0]
    assert reason.reason == SuspicionReason.JUMP
    assert reason.delta == 245
    assert reason.threshold_pages == pytest.approx(SPEED_MULTIPLIER * 2.89)
    assert reason.avg_pages_per_day == 2.89
    assert reason.book_share is None


def test_jump_threshold_boundary():
    # 7 * 2.89 = 20.23: дельта 20 проходит, 21 требует подтверждения
    assert classify_progress_update(0, 20, 319, 2.89) == []
    assert classify_progress_update(0, 21, 319, 2.89)


def test_speed_threshold_has_minimum():
    # 7 * 0.5 = 3.5, но минимальная дельта скачка 10 страниц
    assert classify_progress_update(0, 10, 319, 0.5) == []

    reasons = classify_progress_update(0, 11, 319, 0.5)
    assert len(reasons) == 1
    assert reasons[0].threshold_pages == MIN_JUMP_PAGES
    assert reasons[0].avg_pages_per_day == 0.5


def test_jump_without_history_uses_book_share():
    reasons = classify_progress_update(0, 80, 319, 0.0)

    assert len(reasons) == 1
    reason = reasons[0]
    assert reason.reason == SuspicionReason.JUMP
    assert reason.threshold_pages == pytest.approx(319 * BOOK_SHARE_THRESHOLD)
    assert reason.book_share == BOOK_SHARE_THRESHOLD
    assert reason.avg_pages_per_day is None


def test_jump_without_history_boundary():
    # 25% от 319 = 79.75: дельта 79 проходит, 80 требует подтверждения
    assert classify_progress_update(0, 79, 319, None) == []
    assert classify_progress_update(0, 80, 319, None)


def test_zero_pages_book_has_no_jump_threshold():
    assert classify_progress_update(0, 0, 0, 0.0) == []
