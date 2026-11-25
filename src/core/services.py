"""Сервисный слой для работы с книгами."""

from datetime import date, datetime, timedelta
from math import ceil
from pathlib import Path
from typing import Callable, Dict, List, Optional

from core.db import get_db
from core.models import (
    ACHIEVEMENT_DEFINITIONS,
    DAILY_PAGES_GOAL,
    READING_SPEED_PERIODS,
    AchievementCheckResult,
    AchievementMetric,
    AchievementStatus,
    Book,
    BookCompletionForecast,
    Goal,
    GoalStatus,
    MotivationContext,
    ReadingMetricComparison,
    ReadingPeriodSummary,
    ReadingStatus,
    ReadingSummary,
    User,
)
from core.repository import (
    AchievementRepository,
    BookRepository,
    GoalRepository,
    MotivationPhraseRepository,
    ReadStatsRepository,
    TagRepository,
    UserRepository,
    UserSettingsRepository,
)
from utils import logger
from utils.config import load_config

log = logger.setup_logger(__name__)


class AchievementService:
    """Сервис вычисления и однократного получения достижений."""

    def __init__(self, db_path: str | None = None) -> None:
        db_path = db_path or get_default_db_path()
        db = get_db(db_path)
        self.book_repo = BookRepository(db)
        self.read_stats_repo = ReadStatsRepository(db)
        self.achievement_repo = AchievementRepository(db)

    def check(self, user_id: str, now: datetime | None = None) -> AchievementCheckResult:
        """Проверяет весь каталог и сохраняет новые награды пользователя."""
        checked_at = now or datetime.now()
        total_books, read_books = self.book_repo.count_books_by_user(user_id)
        metrics = {
            AchievementMetric.BOOKS: total_books,
            AchievementMetric.READ_BOOKS: read_books,
            AchievementMetric.PAGES: self.read_stats_repo.fetch_total_pages_by_user(user_id),
        }
        unlocked = self.achievement_repo.get_unlocked(user_id)
        candidates = [
            definition.key
            for definition in ACHIEVEMENT_DEFINITIONS
            if definition.key not in unlocked and metrics[definition.metric] >= definition.target
        ]
        inserted = self.achievement_repo.unlock(user_id, candidates, checked_at)
        if candidates:
            unlocked = self.achievement_repo.get_unlocked(user_id)

        statuses = [
            AchievementStatus(
                definition=definition,
                current=metrics[definition.metric],
                unlocked_at=unlocked.get(definition.key),
            )
            for definition in ACHIEVEMENT_DEFINITIONS
        ]
        inserted_keys = set(inserted)
        new_achievements = [
            definition for definition in ACHIEVEMENT_DEFINITIONS if definition.key in inserted_keys
        ]
        return AchievementCheckResult(statuses=statuses, new_achievements=new_achievements)


class BookService:
    """Сервис для работы с книгами."""

    def __init__(self, db_path: str | None = None) -> None:
        """Инициализация сервиса."""
        db_path = db_path or get_default_db_path()
        db = get_db(db_path)
        self.book_repo = BookRepository(db)
        self.user_repo = UserRepository(db)
        self.tag_repo = TagRepository(db)
        self.reading_stats_service = ReadingStatsService(db_path)

    def filter_books(
        self,
        user_id: str,
        status: str | None = None,
        tags: list[str] | None = None,
    ) -> list[Book]:
        """Возвращает книги, отфильтрованные по статусу и/или тегам.
        Если статус не задан, фильтрация по статусу не применяется.
        Если список тегов пустой или None, фильтрация по тегам не применяется.
        """
        books = self.get_all_books(user_id)
        if status:
            books = [b for b in books if b.status.value == status]
        if tags:
            books = [b for b in books if set(tags).intersection(set(b.tags))]
        return books

    def get_all_tags(self, user_id: str) -> list[str]:
        """Возвращает теги пользователя, привязанные хотя бы к одной книге."""
        return self.tag_repo.get_used_tags(user_id)

    def create_book(
        self,
        title: str,
        author: str,
        tags: list[str],
        pages: int,
        user_id: str,
        current_page: int = 0,
        status: str = ReadingStatus.WANT_TO_READ.value,
        link: Optional[str] = None,
    ) -> Book:
        """Создаёт новую книгу."""
        book = Book(
            title=title,
            author=author,
            tags=tags,
            pages=pages,
            user_id=user_id,
            current_page=current_page,
            status=ReadingStatus(status),
            link=link,
        )
        return self.book_repo.add_book(book)

    def get_all_books(self, user_id: Optional[str] = None) -> List[Book]:
        """Получает все книги. Фильтрует по user_id, если указан.
        Прочитанные книги всегда в конце."""
        books = (
            self.book_repo.get_all_books()
            if user_id is None
            else self.book_repo.get_books_by_user_id(user_id)
        )

        # Прочитанные книги всегда в конце
        books.sort(key=lambda b: b.status == ReadingStatus.READ)

        return books

    def get_stats(self, user_id: Optional[str] = None) -> Dict:
        """Получает общие показатели библиотеки, сохраняя их прежние формулы."""
        books = self.get_all_books(user_id)

        total_books = len(books)
        read_books = len([b for b in books if b.status == ReadingStatus.READ])
        reading_books = len([b for b in books if b.status == ReadingStatus.READING])
        want_to_read_books = len([b for b in books if b.status == ReadingStatus.WANT_TO_READ])
        postponed_books = len([b for b in books if b.status == ReadingStatus.POSTPONED])

        total_pages = sum(b.pages for b in books)
        read_pages = sum(b.current_page for b in books)
        avg_progress = (read_pages / total_pages * 100) if total_pages > 0 else 0

        return {
            "total_books": total_books,
            "read_books": read_books,
            "reading_books": reading_books,
            "want_to_read_books": want_to_read_books,
            "postponed_books": postponed_books,
            "total_pages": total_pages,
            "read_pages": int(read_pages),
            "avg_progress": avg_progress,
        }

    def get_book_by_id(self, book_id: str) -> Optional[Book]:
        """Получает книгу по ID."""
        return self.book_repo.get_book_by_id(book_id)

    def update_book_status(self, book_id: str, status: str) -> Book:
        """Обновляет статус книги."""
        book = self.book_repo.get_book_by_id(book_id)
        if not book:
            raise ValueError(f"Книга с ID {book_id} не найдена")

        book.status = ReadingStatus(status)
        book.updated_at = datetime.now()

        if status == ReadingStatus.READING.value and not book.reading_start_date:
            book.reading_start_date = datetime.now()

        if status == ReadingStatus.READ.value and book.current_page == book.pages:
            book.reading_end_date = datetime.now()

        return self.book_repo.update_book(book)

    def update_book_progress(self, book_id: str, current_page: int) -> Book:
        """Обновляет прогресс чтения и сохраняет статистику."""
        book = self.book_repo.get_book_by_id(book_id)
        if not book:
            raise ValueError(f"Книга с ID {book_id} не найдена")

        # запомним предыдущее количество прочитанных страниц
        previous_page = book.current_page
        book.update_progress(current_page)

        # Автоматически обновляем статус
        if book.current_page == book.pages:
            book.status = ReadingStatus.READ
            book.reading_end_date = datetime.now()
        elif book.current_page > 0:
            if book.status == ReadingStatus.WANT_TO_READ:
                book.status = ReadingStatus.READING
            if not book.reading_start_date and (
                book.status == ReadingStatus.WANT_TO_READ or book.status == ReadingStatus.READING
            ):
                book.reading_start_date = datetime.now()

        # сохраняем запись о статистике чтения (кол-во новых страниц)
        pages_read = book.current_page - previous_page
        if pages_read > 0:
            try:
                self.reading_stats_service.add_record(book.id, pages_read, user_id=book.user_id)
            except Exception as e:
                log.error(f"Failed to add reading stat for book {book.id}: {e}")

        return self.book_repo.update_book(book)

    def delete_book(self, book_id: str) -> Book:
        """Удаляет книгу."""
        return self.book_repo.delete_book(book_id)

    def update_book_tags(self, book_id: str, tags: list[str]) -> Book:
        """Обновляет теги книги."""
        book = self.book_repo.get_book_by_id(book_id)
        if not book:
            raise ValueError(f"Книга с ID {book_id} не найдена")

        book.tags = tags
        book.updated_at = datetime.now()

        return self.book_repo.update_book(book)


class TagService:
    """Сервис персонального набора тегов пользователя."""

    def __init__(self, db_path: str | None = None) -> None:
        """Инициализация сервиса."""
        db_path = db_path or get_default_db_path()
        self.tag_repo = TagRepository(get_db(db_path))

    def get_user_tags(self, user_id: str) -> list[str]:
        """Возвращает набор тегов пользователя (справочник)."""
        return self.tag_repo.get_user_tags(user_id)

    def get_used_tags(self, user_id: str) -> list[str]:
        """Возвращает теги пользователя, привязанные хотя бы к одной его книге."""
        return self.tag_repo.get_used_tags(user_id)


class UserService:
    """Сервис для работы с пользователями."""

    def __init__(self, db_path: str | None = None) -> None:
        """Инициализация сервиса."""
        db_path = db_path or get_default_db_path()
        db = get_db(db_path)
        self.user_repo = UserRepository(db)

    def get_or_create_user(
        self, user_external_id: int, user_factory: Callable[[int], User]
    ) -> User:
        """Получает пользователя или создаёт нового."""
        user = self.user_repo.get_user_by_external_id(user_external_id)

        if not user:
            user = user_factory(user_external_id)
            user = self.user_repo.add_user(user)

        # Обновляем последнюю активность
        user.last_active = datetime.now()
        return self.user_repo.update_user(user)


class ReadingStatsService:
    """Сервис для работы со статистикой чтения книг."""

    def __init__(self, db_path: str | None = None) -> None:
        db_path = db_path or get_default_db_path()
        self.db = get_db(db_path)
        self.read_stats_repo = ReadStatsRepository(self.db)
        self.user_settings_repo = UserSettingsRepository(self.db)

    def add_record(
        self,
        book_id: str,
        pages_read: int,
        read_date: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """Добавляет запись статистики чтения."""
        return self.read_stats_repo.add_reading_stats(book_id, pages_read, read_date, user_id)

    def get_reading_stats(self, book_id: str, from_date: datetime, to_date: datetime) -> int:
        """Возвращает количество прочитанных страниц за период."""
        return self.read_stats_repo.fetch_reading_stats(book_id, from_date, to_date)

    def avg_pages_per_day(self, book: Book, today: date | None = None) -> float:
        """Среднее количество страниц книги за период скорости чтения."""
        reference_day = today or date.today()
        period_days = self.user_settings_repo.get_reading_speed_period(book.user_id)
        reading_start_day = (
            book.reading_start_date.date() if book.reading_start_date else reference_day
        )
        from_day = max(reference_day - timedelta(days=period_days - 1), reading_start_day)
        days = (reference_day - from_day).days + 1
        total = self.read_stats_repo.fetch_reading_stats(
            book.id,
            datetime.combine(from_day, datetime.min.time()),
            datetime.combine(reference_day, datetime.max.time()),
        )
        return total / days if days > 0 else 0.0

    def overall_avg_pages_per_day(self, user_id: str, today: date | None = None) -> float:
        """Среднее количество страниц пользователя по всем книгам за период настройки."""
        reference_day = today or date.today()
        period_days = self.user_settings_repo.get_reading_speed_period(user_id)
        from_day = reference_day - timedelta(days=period_days - 1)
        total = self.read_stats_repo.fetch_pages_by_user(
            user_id,
            datetime.combine(from_day, datetime.min.time()),
            datetime.combine(reference_day, datetime.max.time()),
        )
        return total / period_days

    def predict_days_to_completion(self, book: Book, today: date | None = None) -> int | None:
        """Прогнозирует количество дней до завершения чтения книги."""
        remaining_pages = book.pages - book.current_page
        if remaining_pages <= 0:
            return 0  # книга уже дочитана
        avg = self.avg_pages_per_day(book, today)
        if avg == 0:
            avg = self.overall_avg_pages_per_day(book.user_id, today)
        if avg == 0:
            return None  # недостаточно данных о скорости чтения
        return ceil(remaining_pages / avg)

    def predict_completion_date(self, book: Book, today: date | None = None) -> date | None:
        """Прогнозирует дату завершения чтения книги на основе количества дней."""
        reference_day = today or date.today()
        days_needed = self.predict_days_to_completion(book, reference_day)
        if days_needed is None:
            return None
        return reference_day + timedelta(days=days_needed)


class ReadingSummaryService:
    """Сервис периодических показателей и прогнозов сводки чтения."""

    def __init__(self, db_path: str | None = None) -> None:
        db_path = db_path or get_default_db_path()
        db = get_db(db_path)
        self.book_repo = BookRepository(db)
        self.read_stats_repo = ReadStatsRepository(db)
        self.reading_stats_service = ReadingStatsService(db_path)

    def get_summary(self, user_id: str, today: date | None = None) -> ReadingSummary:
        """Формирует личную сводку на выбранный календарный день."""
        reference_day = today or date.today()
        books = self.book_repo.get_books_by_user_id(user_id)

        week_start = reference_day - timedelta(days=reference_day.weekday())
        previous_week_start = week_start - timedelta(days=7)
        previous_week_end = previous_week_start + (reference_day - week_start)
        week = self._period_summary(
            user_id,
            books,
            week_start,
            reference_day,
            previous_week_start,
            previous_week_end,
        )

        month_start = reference_day.replace(day=1)
        previous_month_last_day = month_start - timedelta(days=1)
        previous_month_start = previous_month_last_day.replace(day=1)
        previous_month_end = previous_month_start.replace(
            day=min(reference_day.day, previous_month_last_day.day)
        )
        month = self._period_summary(
            user_id,
            books,
            month_start,
            reference_day,
            previous_month_start,
            previous_month_end,
        )

        year_start = reference_day.replace(month=1, day=1)
        previous_year_start = year_start.replace(year=year_start.year - 1)
        try:
            previous_year_end = reference_day.replace(year=reference_day.year - 1)
        except ValueError:
            previous_year_end = reference_day.replace(year=reference_day.year - 1, day=28)
        year = self._period_summary(
            user_id,
            books,
            year_start,
            reference_day,
            previous_year_start,
            previous_year_end,
            include_read_books=True,
        )

        reading_books = [book for book in books if book.status == ReadingStatus.READING]
        forecasts = [
            BookCompletionForecast(
                book=book,
                completion_date=self.reading_stats_service.predict_completion_date(
                    book, reference_day
                ),
            )
            for book in reading_books
        ]
        forecasts.sort(
            key=lambda forecast: (
                forecast.completion_date is None,
                forecast.completion_date or date.max,
                forecast.book.title.casefold(),
            )
        )

        want_to_read_books = [book for book in books if book.status == ReadingStatus.WANT_TO_READ]
        overall_speed = self.reading_stats_service.overall_avg_pages_per_day(user_id, reference_day)
        queue_completion_date = self._predict_queue_completion(
            want_to_read_books,
            forecasts,
            overall_speed,
            reference_day,
        )

        return ReadingSummary(
            week=week,
            month=month,
            year=year,
            reading_forecasts=forecasts,
            want_to_read_count=len(want_to_read_books),
            want_to_read_completion_date=queue_completion_date,
        )

    def _period_summary(
        self,
        user_id: str,
        books: list[Book],
        current_start: date,
        current_end: date,
        previous_start: date,
        previous_end: date,
        include_read_books: bool = False,
    ) -> ReadingPeriodSummary:
        pages = ReadingMetricComparison(
            current=self._fetch_pages(user_id, current_start, current_end),
            previous=self._fetch_pages(user_id, previous_start, previous_end),
        )
        read_books = None
        if include_read_books:
            read_books = ReadingMetricComparison(
                current=self._count_read_books(books, current_start, current_end),
                previous=self._count_read_books(books, previous_start, previous_end),
            )
        return ReadingPeriodSummary(pages=pages, read_books=read_books)

    def _fetch_pages(self, user_id: str, from_day: date, to_day: date) -> int:
        return self.read_stats_repo.fetch_pages_by_user(
            user_id,
            datetime.combine(from_day, datetime.min.time()),
            datetime.combine(to_day, datetime.max.time()),
        )

    @staticmethod
    def _count_read_books(books: list[Book], from_day: date, to_day: date) -> int:
        return sum(
            1
            for book in books
            if book.status == ReadingStatus.READ
            and book.reading_end_date is not None
            and from_day <= book.reading_end_date.date() <= to_day
        )

    @staticmethod
    def _predict_queue_completion(
        books: list[Book],
        reading_forecasts: list[BookCompletionForecast],
        overall_speed: float,
        today: date,
    ) -> date | None:
        if not books or overall_speed == 0:
            return None
        if any(forecast.completion_date is None for forecast in reading_forecasts):
            return None
        base_date = max(
            (forecast.completion_date for forecast in reading_forecasts),
            default=today,
        )
        queue_days = ceil(sum(book.pages for book in books) / overall_speed)
        return base_date + timedelta(days=queue_days)


class GoalService:
    """Сервис дневной цели чтения."""

    def __init__(self, db_path: str | None = None) -> None:
        """Инициализация сервиса."""
        db_path = db_path or get_default_db_path()
        db = get_db(db_path)
        self.goal_repo = GoalRepository(db)
        self.read_stats_repo = ReadStatsRepository(db)

    def get_goal(self, user_id: str, kind: str = DAILY_PAGES_GOAL) -> Optional[Goal]:
        """Возвращает цель пользователя или None."""
        return self.goal_repo.get_goal(user_id, kind)

    def set_daily_goal(self, user_id: str, target: int) -> Goal:
        """Устанавливает дневную цель по страницам."""
        if target <= 0:
            raise ValueError("Цель должна быть положительным целым числом")
        return self.goal_repo.upsert_goal(user_id, target)

    def disable_goal(self, user_id: str, kind: str = DAILY_PAGES_GOAL) -> bool:
        """Отключает цель пользователя. Возвращает True, если цель была."""
        return self.goal_repo.delete_goal(user_id, kind)

    def today_pages(self, user_id: str, now: datetime | None = None) -> int:
        """Сколько страниц прочитано сегодня (локальный календарный день сервера)."""
        day_start = (now or datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
        return self.read_stats_repo.fetch_pages_by_user(user_id, day_start, day_end)

    def get_current_streak(self, user_id: str, now: datetime | None = None) -> int | None:
        """Возвращает текущий страйк пользователя или None без дневной цели."""
        goal = self.get_goal(user_id)
        if not goal:
            return None
        return self._calculate_streak(goal, now)

    def _calculate_streak(self, goal: Goal, now: datetime | None = None) -> int:
        """Вычисляет серию по дневным суммам истории загруженной цели."""
        today = (now or datetime.now()).date()
        created_day = goal.created_at.date()
        daily_pages = self.read_stats_repo.fetch_daily_pages_by_user(
            goal.user_id, created_day, today + timedelta(days=1)
        )

        current_day = today
        if daily_pages.get(today, 0) < goal.target:
            current_day -= timedelta(days=1)
        if current_day < created_day or daily_pages.get(current_day, 0) < goal.target:
            return 0

        streak = 0
        while current_day >= created_day and daily_pages.get(current_day, 0) >= goal.target:
            streak += 1
            current_day -= timedelta(days=1)
        return streak

    def get_goal_status(
        self,
        user_id: str,
        kind: str = DAILY_PAGES_GOAL,
        now: datetime | None = None,
    ) -> Optional[GoalStatus]:
        """Возвращает состояние дневной цели или None, если цели нет."""
        goal = self.get_goal(user_id, kind)
        if not goal:
            return None
        pages_today = self.today_pages(user_id, now)
        streak = self._calculate_streak(goal, now)
        percent = min(100, round(pages_today / goal.target * 100)) if goal.target > 0 else 0
        return GoalStatus(
            goal=goal,
            pages_today=pages_today,
            percent=percent,
            completed=pages_today >= goal.target,
            remaining=max(0, goal.target - pages_today),
            streak=streak,
        )


class UserSettingsService:
    """Сервис персональных настроек пользователя."""

    def __init__(self, db_path: str | None = None) -> None:
        """Инициализация сервиса."""
        db_path = db_path or get_default_db_path()
        self.settings_repo = UserSettingsRepository(get_db(db_path))

    def get_reading_speed_period(self, user_id: str) -> int:
        """Возвращает период скорости чтения пользователя."""
        return self.settings_repo.get_reading_speed_period(user_id)

    def set_reading_speed_period(self, user_id: str, days: int) -> None:
        """Сохраняет период скорости чтения пользователя."""
        if days not in READING_SPEED_PERIODS:
            raise ValueError("Период должен быть одним из: 7, 14, 30 дней")
        self.settings_repo.set_reading_speed_period(user_id, days)

    def is_motivation_enabled(self, user_id: str) -> bool:
        """Включена ли мотивация у пользователя (по умолчанию включена)."""
        return self.settings_repo.get_motivation_enabled(user_id)

    def set_motivation_enabled(self, user_id: str, enabled: bool) -> None:
        """Сохраняет настройку мотивации пользователя."""
        self.settings_repo.set_motivation_enabled(user_id, enabled)


class MotivationService:
    """Сервис подбора фразы для отклика на обновление прогресса."""

    def __init__(self, db_path: str | None = None) -> None:
        """Инициализация сервиса."""
        db_path = db_path or get_default_db_path()
        self.phrase_repo = MotivationPhraseRepository(get_db(db_path))

    def pick_phrase(self, context: MotivationContext) -> str | None:
        """Подбирает мотивационную фразу под контекст обновления.

        В v1 стратегия случайная и контекст игнорируется: сценарный выбор
        категорий (тренд, цель, завершение) заменит стратегию позже.
        """
        return self.phrase_repo.get_random_phrase()


def get_default_db_path() -> str:
    config = load_config()
    return str(Path(config.data_dir) / "database.db")
