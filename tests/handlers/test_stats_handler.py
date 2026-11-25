from datetime import date

from conftest import FakeVkApi, make_context

from core.models import (
    Book,
    BookCompletionForecast,
    ReadingMetricComparison,
    ReadingPeriodSummary,
    ReadingSummary,
)
from vk_bot.handlers import stats as stats_module


def _stats():
    return {
        "total_books": 5,
        "read_books": 1,
        "reading_books": 2,
        "want_to_read_books": 2,
        "postponed_books": 0,
        "total_pages": 500,
        "read_pages": 150,
        "avg_progress": 30.0,
    }


def _summary():
    return ReadingSummary(
        week=ReadingPeriodSummary(ReadingMetricComparison(10, 5)),
        month=ReadingPeriodSummary(ReadingMetricComparison(20, 10)),
        year=ReadingPeriodSummary(
            ReadingMetricComparison(100, 80),
            ReadingMetricComparison(2, 1),
        ),
        reading_forecasts=[
            BookCompletionForecast(Book(title="Soon"), date(2026, 12, 1)),
            BookCompletionForecast(Book(title="Unknown"), None),
        ],
        want_to_read_count=2,
        want_to_read_completion_date=date(2026, 12, 20),
    )


def test_stats_handler_sends_personal_reading_summary(monkeypatch):
    fake_api = FakeVkApi()
    requested_user_ids = []
    monkeypatch.setattr(stats_module, "BookService", lambda: _BookServiceStub())
    monkeypatch.setattr(
        stats_module,
        "ReadingSummaryService",
        lambda: _ReadingSummaryServiceStub(requested_user_ids),
    )
    context = make_context(fake_api, 7, "/stats")

    result = stats_module.StatsHandler().handle(context)

    assert result is True
    assert requested_user_ids == ["user-7"]
    assert len(fake_api.sent_messages) == 1
    assert fake_api.sent_messages[0]["message"] == (
        "📊 Сводка чтения\n\n"
        "Всего книг: 5\n"
        "Прочитано: 1\n"
        "Читаю сейчас: 2\n"
        "Хочу прочитать: 2\n"
        "Отложено: 0\n\n"
        "Всего страниц: 500\n"
        "Прочитано страниц: 150\n"
        "Средний прогресс: 30.0%\n\n"
        "📅 Периоды\n"
        "Неделя: 10 стр. (было 5, +5)\n"
        "Месяц: 20 стр. (было 10, +10)\n"
        "Год: 100 стр. (было 80, +20)\n"
        "Книги за год: 2 кн. (было 1, +1)\n\n"
        "📚 Прогноз книг «Читаю»\n"
        "• Soon — 2026-12-01\n"
        "• Unknown — недостаточно данных\n\n"
        "🗂 Прогноз очереди «Хочу прочитать»\n"
        "Книг в очереди: 2\n"
        "Дата завершения всей очереди: 2026-12-20"
    )


def test_reading_summary_formats_empty_sections():
    summary = ReadingSummary(
        week=ReadingPeriodSummary(ReadingMetricComparison(0, 0)),
        month=ReadingPeriodSummary(ReadingMetricComparison(0, 0)),
        year=ReadingPeriodSummary(
            ReadingMetricComparison(0, 0),
            ReadingMetricComparison(0, 0),
        ),
        reading_forecasts=[],
        want_to_read_count=0,
        want_to_read_completion_date=None,
    )

    text = stats_module.format_reading_summary(_stats(), summary)

    assert "Сейчас нет книг со статусом «Читаю»." in text
    assert "Очередь пуста." in text
    assert "Неделя: 0 стр. (было 0, +0)" in text


class _BookServiceStub:
    def get_stats(self, user_id):
        assert user_id == "user-7"
        return _stats()


class _ReadingSummaryServiceStub:
    def __init__(self, requested_user_ids):
        self.requested_user_ids = requested_user_ids

    def get_summary(self, user_id):
        self.requested_user_ids.append(user_id)
        return _summary()
