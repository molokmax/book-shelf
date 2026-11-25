"""Обработчик одношаговой команды `/stats` и форматирование сводки чтения."""

from typing import Any

from core.models import ReadingMetricComparison, ReadingSummary
from core.services import BookService, ReadingSummaryService
from vk_bot.keyboards import main_keyboard
from vk_bot.user_helpers import get_or_create_user

from ..context import BotContext
from .base import AbstractCommandHandler


def _format_comparison(metric: ReadingMetricComparison, unit: str) -> str:
    return f"{metric.current} {unit} (было {metric.previous}, {metric.difference:+d})"


def format_reading_summary(stats: dict, summary: ReadingSummary) -> str:
    """Форматирует общие показатели, периоды и прогнозы одним сообщением."""
    lines = [
        "📊 Сводка чтения",
        "",
        f"Всего книг: {stats['total_books']}",
        f"Прочитано: {stats['read_books']}",
        f"Читаю сейчас: {stats['reading_books']}",
        f"Хочу прочитать: {stats['want_to_read_books']}",
        f"Отложено: {stats['postponed_books']}",
        "",
        f"Всего страниц: {stats['total_pages']}",
        f"Прочитано страниц: {stats['read_pages']}",
        f"Средний прогресс: {stats['avg_progress']:.1f}%",
        "",
        "📅 Периоды",
        f"Неделя: {_format_comparison(summary.week.pages, 'стр.')}",
        f"Месяц: {_format_comparison(summary.month.pages, 'стр.')}",
        f"Год: {_format_comparison(summary.year.pages, 'стр.')}",
    ]
    if summary.year.read_books is not None:
        lines.append(f"Книги за год: {_format_comparison(summary.year.read_books, 'кн.')}")

    lines.extend(["", "📚 Прогноз книг «Читаю»"])
    if summary.reading_forecasts:
        for forecast in summary.reading_forecasts:
            completion = (
                forecast.completion_date.strftime("%Y-%m-%d")
                if forecast.completion_date is not None
                else "недостаточно данных"
            )
            lines.append(f"• {forecast.book.title} — {completion}")
    else:
        lines.append("Сейчас нет книг со статусом «Читаю».")

    lines.extend(["", "🗂 Прогноз очереди «Хочу прочитать»"])
    if summary.want_to_read_count == 0:
        lines.append("Очередь пуста.")
    else:
        lines.append(f"Книг в очереди: {summary.want_to_read_count}")
        if summary.want_to_read_completion_date is None:
            lines.append("Недостаточно данных о скорости чтения для прогноза.")
        else:
            completion = summary.want_to_read_completion_date.strftime("%Y-%m-%d")
            lines.append(f"Дата завершения всей очереди: {completion}")

    return "\n".join(lines)


class StatsHandler(AbstractCommandHandler):
    """Отображает личную сводку чтения пользователя."""

    priority = 10
    commands = ["/stats", "stats"]

    def _handle(self, context: BotContext) -> Any:
        api = context.api
        user_id = context.user_id
        user = get_or_create_user(api, user_id)

        stats = BookService().get_stats(user.id)
        summary = ReadingSummaryService().get_summary(user.id)
        stats_text = format_reading_summary(stats, summary)

        context.send_message(stats_text, keyboard=main_keyboard())
        return True
