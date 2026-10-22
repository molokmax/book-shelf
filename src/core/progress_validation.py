"""Классификация обновлений прогресса чтения.

Модуль не зависит от бота и базы данных: принимает числа и возвращает
причины, по которым обновление нужно подтвердить у пользователя.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

# Во сколько раз дельта может превысить среднюю скорость чтения.
SPEED_MULTIPLIER = 7
# Минимальная дельта скачка, чтобы низкая средняя скорость не давала ложных срабатываний.
MIN_JUMP_PAGES = 10
# Доля страниц книги для скачка, когда данных о скорости чтения нет.
BOOK_SHARE_THRESHOLD = 0.25


class SuspicionReason(str, Enum):
    """Причина, по которой обновление прогресса требует подтверждения."""

    ROLLBACK = "rollback"
    JUMP = "jump"


@dataclass(frozen=True)
class Suspicion:
    """Причина подтверждения и данные для текста сообщения."""

    reason: SuspicionReason
    previous_page: int
    new_page: int
    pages: int
    threshold_pages: Optional[float] = None
    avg_pages_per_day: Optional[float] = None
    book_share: Optional[float] = None

    @property
    def delta(self) -> int:
        """Разница между новым и текущим значением прогресса."""
        return self.new_page - self.previous_page


def classify_progress_update(
    previous_page: int,
    new_page: int,
    pages: int,
    avg_pages_per_day: Optional[float],
) -> list[Suspicion]:
    """Возвращает причины, по которым обновление прогресса подозрительно.

    Пустой список означает, что значение можно применять без подтверждения.
    Откат проверяется при любом движении назад, скачок только при движении вперёд.
    """
    if new_page < previous_page:
        return [
            Suspicion(
                reason=SuspicionReason.ROLLBACK,
                previous_page=previous_page,
                new_page=new_page,
                pages=pages,
            )
        ]

    if new_page == previous_page:
        return []

    threshold, avg, share = _jump_threshold(pages, avg_pages_per_day)
    if threshold is None or new_page - previous_page <= threshold:
        return []

    return [
        Suspicion(
            reason=SuspicionReason.JUMP,
            previous_page=previous_page,
            new_page=new_page,
            pages=pages,
            threshold_pages=threshold,
            avg_pages_per_day=avg,
            book_share=share,
        )
    ]


def _jump_threshold(
    pages: int, avg_pages_per_day: Optional[float]
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Возвращает порог скачка и данные, объясняющие его происхождение.

    При известной скорости порог равен max(7 * avg, 10) страниц.
    Без истории чтения порог равен 25% страниц книги.
    """
    if avg_pages_per_day and avg_pages_per_day > 0:
        threshold = max(SPEED_MULTIPLIER * avg_pages_per_day, MIN_JUMP_PAGES)
        return threshold, avg_pages_per_day, None
    if pages > 0:
        return pages * BOOK_SHARE_THRESHOLD, None, BOOK_SHARE_THRESHOLD
    return None, None, None
