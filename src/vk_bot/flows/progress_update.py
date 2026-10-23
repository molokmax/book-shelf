"""Общая логика запроса, проверки и применения прогресса чтения."""

from datetime import datetime, timedelta

from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id

from core.progress_validation import (
    Suspicion,
    SuspicionReason,
    classify_progress_update,
)
from core.services import BookService, GoalService, ReadingStatsService
from utils import helpers, logger
from vk_bot.context import BotContext
from vk_bot.keyboards import cancel_keyboard, main_keyboard

log = logger.setup_logger(__name__)


class ProgressUpdateFlow:
    """Сценарий обновления прогресса книги.

    Используется новым ``ProgressHandler`` и legacy-состояниями ``EditHandler``.
    Сохраняет ``command`` из переданного состояния, чтобы не ломать маршрутизацию.
    """

    def start(self, context: BotContext, state_info: dict, book) -> None:
        """Запрашивает текущую страницу для книги."""
        state_info["state"] = "waiting_for_progress_input"
        state_info.setdefault("data", {})["progress_book_pages"] = book.pages
        state_info["data"].pop("pending_progress_page", None)
        context.set_state(state_info)

        percent = helpers.get_progress_percent(book.current_page, book.pages)
        self._send(
            context,
            (
                f"📖 Книга: {book.title}\n"
                f"Прогресс: {book.current_page}/{book.pages} ({percent}%)\n\n"
                f"Введи текущую страницу (от 0 до {book.pages})."
            ),
            cancel_keyboard(),
        )

    def handle(self, context: BotContext) -> None:
        """Обрабатывает текущее состояние обновления прогресса."""
        state_info = context.get_state()
        state = state_info.get("state")
        if state == "waiting_for_progress_input":
            self._handle_input(context, state_info)
        elif state == "waiting_for_progress_confirm":
            self._handle_confirm(context, state_info)

    def _handle_input(self, context: BotContext, state_info: dict) -> None:
        value, error = self._parse_progress_value(
            context.text, state_info["data"].get("progress_book_pages")
        )
        if error:
            self._send(context, error, cancel_keyboard())
            return

        self._submit_progress_value(context, state_info, value)

    def _handle_confirm(self, context: BotContext, state_info: dict) -> None:
        if context.text.strip().lower() == "продолжить":
            pending_page = state_info["data"].get("pending_progress_page")
            if pending_page is None:
                self._send(
                    context,
                    "⚠️ Нечего подтверждать: значение прогресса потеряно.",
                    cancel_keyboard(),
                )
                return
            self._apply_progress(context, state_info, pending_page)
            return

        value, error = self._parse_progress_value(
            context.text, state_info["data"].get("progress_book_pages")
        )
        if error:
            self._send(context, error, self._create_progress_confirm_keyboard())
            return

        self._submit_progress_value(context, state_info, value)

    def _submit_progress_value(self, context: BotContext, state_info: dict, new_page: int) -> None:
        """Применяет значение или запрашивает подтверждение, если оно подозрительно."""
        book_id = state_info["data"].get("selected_book_id")
        if not book_id:
            self._send(
                context,
                "⚠️ Идентификатор книги не найден.",
                cancel_keyboard(),
            )
            return

        book = BookService().get_book_by_id(book_id)
        if not book:
            self._send(context, "⚠️ Книга не найдена.", cancel_keyboard())
            return

        if new_page == book.current_page:
            self._finish_progress_update(context, book, unchanged=True)
            return

        reasons = classify_progress_update(
            previous_page=book.current_page,
            new_page=new_page,
            pages=book.pages,
            avg_pages_per_day=self._avg_pages_per_day(book),
        )
        if not reasons:
            self._apply_progress(context, state_info, new_page)
            return

        state_info["state"] = "waiting_for_progress_confirm"
        state_info["data"]["pending_progress_page"] = new_page
        context.set_state(state_info)
        self._send(
            context,
            self._format_progress_confirm_message(book, new_page, reasons),
            self._create_progress_confirm_keyboard(),
        )

    def _apply_progress(self, context: BotContext, state_info: dict, new_page: int) -> None:
        book_id = state_info["data"].get("selected_book_id")
        if not book_id:
            self._send(
                context,
                "⚠️ Идентификатор книги не найден.",
                cancel_keyboard(),
            )
            return

        service = BookService()
        previous_book = service.get_book_by_id(book_id)
        previous_page = previous_book.current_page if previous_book else 0
        updated_book = service.update_book_progress(book_id, new_page)
        pages_delta = max(0, updated_book.current_page - previous_page)
        self._finish_progress_update(
            context, updated_book, unchanged=False, pages_delta=pages_delta
        )

    def _finish_progress_update(
        self, context: BotContext, book, unchanged: bool, pages_delta: int = 0
    ) -> None:
        progress_stats = self._build_progress_stats(book)
        if unchanged:
            percent = helpers.get_progress_percent(book.current_page, book.pages)
            header = f"ℹ️ Прогресс не изменился: {book.current_page}/{book.pages} ({percent}%)."
        else:
            header = f"✅ Прогресс чтения книги '{book.title}' обновлён."

        parts = [header, progress_stats]
        goal_line = self._format_goal_progress(book, pages_delta)
        if goal_line:
            parts.append(goal_line)

        self._send(context, "\n\n".join(parts), main_keyboard())
        context.delete_state()

    def _format_goal_progress(self, book, pages_delta: int) -> str | None:
        """Строка о дневной цели; None, если цели нет или нет владельца книги."""
        user_id = getattr(book, "user_id", None)
        if not user_id:
            return None

        try:
            service = GoalService()
            goal = service.get_goal(user_id)
            if not goal:
                return None
            pages_today = service.today_pages(user_id)
        except Exception as e:
            log.error(f"Failed to build daily goal progress for book {book.id}: {e}")
            return None

        if pages_delta > 0 and pages_today - pages_delta < goal.target <= pages_today:
            return (
                "🎉 Цель на день выполнена! "
                f"Сегодня прочитано {pages_today} из {goal.target} страниц."
            )
        return f"Цель на день: {pages_today}/{goal.target} стр."

    @staticmethod
    def _avg_pages_per_day(book) -> float:
        """Средняя скорость чтения книги, 0 при недоступной статистике."""
        try:
            return ReadingStatsService().avg_pages_per_day(book)
        except Exception as e:
            log.error(f"Failed to calculate average pages per day for book {book.id}: {e}")
            return 0.0

    def _build_progress_stats(self, book) -> str:
        """Собирает мини-статистику по книге для ответа пользователю."""
        stats_service = ReadingStatsService()
        today = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        week_start = (today - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = (today - timedelta(days=30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        weekly_pages = stats_service.get_reading_stats(book.id, week_start, today)
        monthly_pages = stats_service.get_reading_stats(book.id, month_start, today)
        avg_pages = stats_service.avg_pages_per_day(book)
        days_left = stats_service.predict_days_to_completion(book)
        predicted_date = stats_service.predict_completion_date(book)
        return helpers.format_progress_stats(
            book,
            weekly_pages=weekly_pages,
            monthly_pages=monthly_pages,
            avg_pages=avg_pages,
            days_to_completion=days_left,
            predicted_date=predicted_date,
        )

    def _format_progress_confirm_message(
        self, book, new_page: int, reasons: list[Suspicion]
    ) -> str:
        current_percent = helpers.get_progress_percent(book.current_page, book.pages)
        new_percent = helpers.get_progress_percent(new_page, book.pages)
        reason_lines = "\n".join(self._format_suspicion_reason(reason) for reason in reasons)
        return (
            "⚠️ Проверь новое значение\n\n"
            f"📖 Книга: {book.title}\n\n"
            f"Текущий прогресс: {book.current_page}/{book.pages} ({current_percent}%)\n"
            f"Новое значение: {new_page}/{book.pages} ({new_percent}%)\n\n"
            f"Причины:\n{reason_lines}\n\n"
            "Нажми «Продолжить» или введи другое число."
        )

    @staticmethod
    def _format_suspicion_reason(suspicion: Suspicion) -> str:
        if suspicion.reason == SuspicionReason.ROLLBACK:
            return f"- Откат: на {abs(suspicion.delta)} стр. меньше"
        if suspicion.avg_pages_per_day is not None:
            return (
                f"- Скачок: +{suspicion.delta} стр., больше обычного за неделю "
                f"({suspicion.avg_pages_per_day:.2f} стр/день)"
            )
        share = int(round((suspicion.book_share or 0) * 100))
        return f"- Скачок: +{suspicion.delta} стр., больше {share}% книги"

    @staticmethod
    def _parse_progress_value(text: str, total_pages: int | None) -> tuple[int | None, str | None]:
        """Парсит и проверяет ввод прогресса. Возвращает значение или текст ошибки."""
        try:
            value = int(text.strip())
        except ValueError:
            return None, helpers.format_invalid_input("Введи число (например: '50').")

        if total_pages is None:
            return None, helpers.format_invalid_input("Неизвестное количество страниц книги.")
        if value < 0:
            return None, helpers.format_invalid_input("Страница не может быть отрицательной.")
        if value > total_pages:
            return None, helpers.format_invalid_input(
                f"Книга содержит только {total_pages} страниц."
            )
        return value, None

    @staticmethod
    def _create_progress_confirm_keyboard() -> VkKeyboard:
        """Клавиатура подтверждения подозрительного значения прогресса."""
        kb = VkKeyboard()
        kb.add_button("Продолжить")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb

    @staticmethod
    def _send(context: BotContext, message: str, keyboard: VkKeyboard) -> None:
        context.api.messages.send(
            user_id=context.user_id,
            message=message,
            keyboard=keyboard.get_keyboard(),
            random_id=get_random_id(),
        )
