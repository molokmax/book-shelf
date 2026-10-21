"""Тесты хелперов форматирования."""

from datetime import date, datetime

from core.models import ReadingStatus
from utils.helpers import format_book_details, format_progress_stats


class FakeBook:
    def __init__(self, current_page=0, pages=0):
        self.current_page = current_page
        self.pages = pages


class FakeDetailsBook:
    def __init__(self, current_page=55, pages=319):
        self.title = "Book"
        self.author = "Author"
        self.link = None
        self.tags = []
        self.status = ReadingStatus.READING
        self.current_page = current_page
        self.pages = pages
        self.created_at = datetime(2026, 1, 1)
        self.reading_start_date = None


def test_format_progress_stats_full_block():
    book = FakeBook(current_page=55, pages=319)
    result = format_progress_stats(
        book,
        weekly_pages=20,
        monthly_pages=55,
        avg_pages=2.89,
        days_to_completion=78,
        predicted_date=date(2027, 1, 7),
    )
    lines = result.splitlines()
    assert lines == [
        "Прогресс: 55/319 (17%)",
        "За неделю прочитано: 20 стр.",
        "За месяц прочитано: 55 стр.",
        "Среднее за 30 дней: 2.89 стр/день",
        "Осталось: 78 дн.",
        "Дата завершения: 2027-01-07",
    ]


def test_format_progress_stats_zero_average():
    book = FakeBook(current_page=55, pages=319)
    result = format_progress_stats(
        book,
        weekly_pages=20,
        monthly_pages=55,
        avg_pages=0,
        days_to_completion=None,
        predicted_date=None,
    )
    assert "Недостаточно данных для оценки завершения" in result
    assert "Среднее за 30 дней" not in result
    assert "Осталось" not in result
    assert "Дата завершения" not in result


def test_format_progress_stats_zero_pages():
    book = FakeBook(current_page=0, pages=0)
    result = format_progress_stats(
        book,
        avg_pages=0,
        days_to_completion=0,
        predicted_date=date(2026, 10, 21),
    )
    # Прогноз невозможен и блок прогноза подавлен
    assert result == "Прогресс: 0/0 (0%)"


def test_format_progress_stats_finished_book_suppresses_forecast():
    book = FakeBook(current_page=319, pages=319)
    result = format_progress_stats(
        book,
        weekly_pages=20,
        monthly_pages=55,
        avg_pages=2.89,
        days_to_completion=0,
        predicted_date=date(2026, 10, 21),
    )
    lines = result.splitlines()
    assert lines == [
        "Прогресс: 319/319 (100%)",
        "За неделю прочитано: 20 стр.",
        "За месяц прочитано: 55 стр.",
        "Среднее за 30 дней: 2.89 стр/день",
    ]


def test_format_book_details_full_block():
    book = FakeDetailsBook(current_page=55, pages=319)
    result = format_book_details(
        book,
        weekly_pages=20,
        monthly_pages=55,
        avg_pages=2.89,
        days_to_completion=78,
        predicted_date=date(2027, 1, 7),
    )
    lines = result.splitlines()
    assert lines == [
        "📖 Book",
        "Автор: Author",
        "Ссылка: —",
        "Тэги: —",
        "Статус: Читаю",
        "Прогресс: 55/319 (17%)",
        "Дата добавления: 2026-01-01",
        "Дата начала чтения: —",
        "За неделю прочитано: 20 стр.",
        "За месяц прочитано: 55 стр.",
        "Среднее за 30 дней: 2.89 стр/день",
        "Осталось: 78 дн.",
        "Дата завершения: 2027-01-07",
    ]


def test_format_book_details_zero_average():
    book = FakeDetailsBook(current_page=55, pages=319)
    result = format_book_details(
        book,
        weekly_pages=20,
        monthly_pages=55,
        avg_pages=0,
        days_to_completion=None,
        predicted_date=None,
    )
    assert "Недостаточно данных для оценки завершения" in result
    assert "Среднее за 30 дней" not in result
    assert "Осталось" not in result
    assert "Дата завершения" not in result


def test_format_book_details_finished_book_suppresses_forecast():
    book = FakeDetailsBook(current_page=319, pages=319)
    result = format_book_details(
        book,
        weekly_pages=20,
        monthly_pages=55,
        avg_pages=0,
        days_to_completion=0,
        predicted_date=date(2026, 10, 21),
    )
    # Дочитанной книге прогноз не нужен, даже с нулевой скоростью
    assert "Среднее за 30 дней" not in result
    assert "Недостаточно данных" not in result
    assert "Осталось" not in result
    assert "Дата завершения" not in result
