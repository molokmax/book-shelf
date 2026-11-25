"""Модели данных для Book Shelf."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ReadingStatus(str, Enum):
    """Статусы чтения книги."""

    WANT_TO_READ = "want_to_read"
    READING = "reading"
    READ = "read"
    POSTPONED = "postponed"


# Вид дневной цели чтения: количество страниц в день.
DAILY_PAGES_GOAL = "daily_pages"

# Возможные периоды скорости чтения (за сколько дней считать среднее).
READING_SPEED_PERIODS = (7, 14, 30)
# Период по умолчанию при отсутствии сохранённых настроек пользователя.
DEFAULT_READING_SPEED_PERIOD = 30

# Категории мотивационных фраз (сценарный подбор появится позже, v1 — random).
GENERAL_PHRASE_CATEGORY = "general"
PHRASE_CATEGORIES = (GENERAL_PHRASE_CATEGORY, "trend_up", "trend_down", "goal_reached")


class AchievementMetric(str, Enum):
    """Метрики, по которым выдаются достижения."""

    BOOKS = "books"
    READ_BOOKS = "read_books"
    PAGES = "pages"


@dataclass(frozen=True)
class AchievementDefinition:
    """Открытое определение достижения из фиксированного каталога."""

    key: str
    title: str
    description: str
    metric: AchievementMetric
    target: int


@dataclass(frozen=True)
class AchievementStatus:
    """Текущий прогресс и дата получения достижения пользователем."""

    definition: AchievementDefinition
    current: int
    unlocked_at: Optional[datetime] = None

    @property
    def is_unlocked(self) -> bool:
        return self.unlocked_at is not None


@dataclass(frozen=True)
class AchievementCheckResult:
    """Результат полной проверки каталога достижений пользователя."""

    statuses: list[AchievementStatus]
    new_achievements: list[AchievementDefinition]


ACHIEVEMENT_DEFINITIONS = (
    AchievementDefinition(
        key="books_1",
        title="Первая книга",
        description="Добавь 1 книгу в библиотеку.",
        metric=AchievementMetric.BOOKS,
        target=1,
    ),
    AchievementDefinition(
        key="books_10",
        title="Своя библиотека",
        description="Собери библиотеку из 10 книг.",
        metric=AchievementMetric.BOOKS,
        target=10,
    ),
    AchievementDefinition(
        key="read_books_1",
        title="Первый финиш",
        description="Отметь 1 книгу как прочитанную.",
        metric=AchievementMetric.READ_BOOKS,
        target=1,
    ),
    AchievementDefinition(
        key="read_books_5",
        title="Читатель",
        description="Отметь 5 книг как прочитанные.",
        metric=AchievementMetric.READ_BOOKS,
        target=5,
    ),
    AchievementDefinition(
        key="pages_100",
        title="Сотня страниц",
        description="Прочитай 100 страниц по статистике чтения.",
        metric=AchievementMetric.PAGES,
        target=100,
    ),
    AchievementDefinition(
        key="pages_1000",
        title="Тысяча страниц",
        description="Прочитай 1000 страниц по статистике чтения.",
        metric=AchievementMetric.PAGES,
        target=1000,
    ),
)


@dataclass
class Book:
    """Модель книги."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)
    pages: int = 0
    current_page: int = 0
    status: ReadingStatus = ReadingStatus.WANT_TO_READ
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    cover_image: Optional[str] = None
    link: Optional[str] = None
    notes: Optional[str] = None
    reading_start_date: Optional[datetime] = None
    reading_end_date: Optional[datetime] = None
    user_id: str = ""

    def update_progress(self, new_page: int) -> None:
        """Обновляет прогресс чтения по текущей странице."""
        self.current_page = max(0, min(self.pages, new_page))
        self.updated_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        """Создаёт книгу из словаря."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            author=data.get("author", ""),
            tags=data.get("tags", []),
            pages=data.get("pages", 0),
            current_page=data.get("current_page", data.get("progress", 0)),  # Поддержка миграции
            status=ReadingStatus(data.get("status", ReadingStatus.WANT_TO_READ.value)),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            cover_image=data.get("cover_image"),
            notes=data.get("notes"),
            link=data.get("link"),
            reading_start_date=(
                datetime.fromisoformat(data.get("reading_start_date", ""))
                if data.get("reading_start_date")
                else None
            ),
            reading_end_date=(
                datetime.fromisoformat(data.get("reading_end_date", ""))
                if data.get("reading_end_date")
                else None
            ),
            user_id=data.get("user_id", ""),
        )


@dataclass
class User:
    """Модель пользователя."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    external_id: int = 0
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Создаёт пользователя из словаря."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            external_id=data.get("external_id", 0),
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            last_active=datetime.fromisoformat(data.get("last_active", datetime.now().isoformat())),
        )


@dataclass
class ReadStat:
    """Модель статистики чтения книги."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    book_id: str = ""
    pages_read: int = 0
    read_date: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ReadStat":
        """Создаёт объект ReadStat из словаря."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            book_id=data.get("book_id", ""),
            pages_read=data.get("pages_read", 0),
            read_date=datetime.fromisoformat(data.get("read_date", datetime.now().isoformat())),
            user_id=data.get("user_id"),
        )


@dataclass
class Goal:
    """Цель пользователя (сейчас — дневная цель по страницам)."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    kind: str = DAILY_PAGES_GOAL
    target: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class GoalStatus:
    """Состояние дневной цели на текущий момент."""

    goal: Goal
    pages_today: int
    percent: int
    completed: bool
    remaining: int
    streak: int


@dataclass
class MotivationPhrase:
    """Мотивационная фраза в отклике на обновление прогресса."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    category: str = GENERAL_PHRASE_CATEGORY
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MotivationContext:
    """Контекст обновления прогресса для подбора мотивационной фразы.

    В v1 подбор случайный и контекст игнорируется; поля остаются швом
    под будущий сценарный выбор (тренд, цель, завершение книги).
    """

    previous_page: int = 0
    new_page: int = 0
    pages_delta: int = 0
    finished: bool = False
    goal_completed: bool = False
