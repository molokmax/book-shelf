"""Тесты хелперов форматирования."""

from datetime import date

from utils.helpers import format_progress_stats


class FakeBook:
    def __init__(self, current_page=0, pages=0):
        self.current_page = current_page
        self.pages = pages


def test_format_progress_stats_full_block():
    book = FakeBook(current_page=55, pages=319)
    result = format_progress_stats(
        book,
        weekly_pages=20,
        monthly_pages=55,
        avg_pages=2.89,
        predicted_date=date(2027, 1, 7),
    )
    lines = result.splitlines()
    assert lines == [
        "Прогресс: 55/319 (17%)",
        "За последнюю неделю прочитано: 20 стр.",
        "За последний месяц прочитано: 55 стр.",
        "Среднее за 30 дней: 2.89 стр/день",
        "Ожидаемая дата завершения: 2027-01-07",
    ]


def test_format_progress_stats_zero_average():
    book = FakeBook(current_page=55, pages=319)
    result = format_progress_stats(
        book,
        weekly_pages=20,
        monthly_pages=55,
        avg_pages=0,
        predicted_date=None,
    )
    assert "Недостаточно данных для оценки завершения" in result
    assert "Среднее за 30 дней" not in result
    assert "Ожидаемая дата завершения" not in result


def test_format_progress_stats_zero_pages():
    book = FakeBook(current_page=0, pages=0)
    assert format_progress_stats(book) == "Прогресс: 0/0 (0%)"
