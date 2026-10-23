import json
import types
from datetime import date
from unittest.mock import MagicMock

import pytest

from vk_bot.flows import progress_update as puf


class FakeStateStorage:
    def __init__(self):
        self._data = {}

    def get(self, user_id):
        return self._data.get(user_id, {})

    def save(self, user_id, state):
        self._data[user_id] = state

    def delete(self, user_id):
        self._data.pop(user_id, None)

    def is_active(self, user_id):
        return bool(self._data.get(user_id))

    def get_command(self, user_id):
        state = self._data.get(user_id)
        return state.get("command") if state else None


def make_context(api, user_id, text="", payload=None, storage=None):
    vk = MagicMock()
    vk.get_api.return_value = api
    upload = MagicMock()
    event = MagicMock()
    event.user_id = user_id
    event.peer_id = user_id
    event.text = text
    event.payload = json.dumps(payload) if payload else None
    from vk_bot.context import BotContext

    return BotContext(vk=vk, upload=upload, event=event, storage=storage or FakeStateStorage())


class FakeVkApiMethod:
    def __init__(self):
        self.sent_messages = []
        self.messages = self

    def send(self, **kwargs):
        self.sent_messages.append(kwargs)


class ProgressBook:
    def __init__(self, book_id="1", title="Book1", current_page=55, pages=319, user_id=None):
        self.id = book_id
        self.title = title
        self.current_page = current_page
        self.pages = pages
        self.user_id = user_id


def make_progress_book_service(current_page=55, pages=319, updates=None, user_id=None):
    updates = updates if updates is not None else []

    class StubProgressBookService:
        def __init__(self, *args, **kwargs):
            pass

        def get_book_by_id(self, book_id):
            return ProgressBook(
                book_id=book_id, current_page=current_page, pages=pages, user_id=user_id
            )

        def update_book_progress(self, book_id, new_page):
            updates.append(new_page)
            return ProgressBook(
                book_id=book_id, current_page=new_page, pages=pages, user_id=user_id
            )

    return StubProgressBookService


def make_goal_stub(target=None, pages_today=0):
    class StubGoalService:
        def __init__(self, *args, **kwargs):
            pass

        def get_goal(self, user_id):
            return types.SimpleNamespace(target=target) if target is not None else None

        def today_pages(self, user_id):
            return pages_today

    return StubGoalService


def make_stats_stub(weekly=20, monthly=55, avg=2.89, predicted=date(2027, 1, 7)):
    class StubReadingStatsService:
        def __init__(self, *args, **kwargs):
            pass

        def get_reading_stats(self, book_id, from_date, to_date):
            return weekly if (to_date - from_date).days <= 8 else monthly

        def avg_pages_per_day(self, book):
            return avg

        def predict_days_to_completion(self, book):
            if predicted is None:
                return None
            return (predicted - date.today()).days

        def predict_completion_date(self, book):
            return predicted

    return StubReadingStatsService


def save_progress_state(storage, user_id, state="waiting_for_progress_input", **data):
    storage.save(
        user_id,
        {
            "command": "/progress",
            "state": state,
            "data": {"selected_book_id": "1", "progress_book_pages": 319, **data},
        },
    )


def test_progress_prompt_uses_formatted_message():
    fake_api = FakeVkApiMethod()
    user_id = 2000
    storage = FakeStateStorage()
    state_info = {
        "command": "/progress",
        "state": "selecting_reading_book",
        "data": {"selected_book_id": "1", "user_id": "test_user"},
    }
    storage.save(user_id, state_info)
    ctx = make_context(fake_api, user_id, "", storage=storage)

    puf.ProgressUpdateFlow().start(ctx, state_info, ProgressBook())

    msg = fake_api.sent_messages[-1]["message"]
    assert msg == (
        "📖 Книга: Book1\n\n" "Прогресс: 55/319 (17%)\n\n" "Введи текущую страницу (от 0 до 319)."
    )
    assert storage.get(user_id)["state"] == "waiting_for_progress_input"


def test_progress_update_shows_reading_stats(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 999
    storage = FakeStateStorage()
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service())
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())

    ctx = make_context(fake_api, user_id, "65", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    expected_days = (date(2027, 1, 7) - date.today()).days
    assert "Прогресс: 65/319 (20%)" in msg
    assert "За неделю прочитано: 20 стр." in msg
    assert "За месяц прочитано: 55 стр." in msg
    assert "Среднее за 30 дней: 2.89 стр/день" in msg
    assert f"Осталось: {expected_days} дн." in msg
    assert "Дата завершения: 2027-01-07" in msg
    assert "обновлён" in msg
    assert not storage.is_active(user_id)


def test_progress_update_without_data_shows_notice(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 1000
    storage = FakeStateStorage()
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service())
    monkeypatch.setattr(
        puf,
        "ReadingStatsService",
        make_stats_stub(weekly=0, monthly=0, avg=0, predicted=None),
    )

    ctx = make_context(fake_api, user_id, "65", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "Недостаточно данных для оценки завершения" in msg
    assert "Среднее за 30 дней" not in msg
    assert "Осталось" not in msg
    assert "Дата завершения" not in msg


def test_progress_update_finished_book_suppresses_forecast(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 1002
    storage = FakeStateStorage()
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(current_page=300))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())

    ctx = make_context(fake_api, user_id, "319", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "Прогресс: 319/319 (100%)" in msg
    assert "Среднее за 30 дней: 2.89 стр/день" in msg
    assert "Осталось" not in msg
    assert "Дата завершения" not in msg
    assert "Недостаточно данных" not in msg


def test_progress_update_invalid_input_has_no_stats(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 1001
    storage = FakeStateStorage()
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service())
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())

    ctx = make_context(fake_api, user_id, "abc", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert msg.startswith("⚠️ Не удалось обработать сообщение.")
    assert "Введи число" in msg
    assert "Прогресс: 55/319" not in msg
    assert storage.is_active(user_id)


def test_rollback_requires_confirmation(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 2001
    storage = FakeStateStorage()
    updates = []
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(updates=updates))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())

    ctx = make_context(fake_api, user_id, "25", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "⚠️ Проверь новое значение" in msg
    assert "Текущий прогресс: 55/319 (17%)" in msg
    assert "Новое значение: 25/319 (8%)" in msg
    assert "- Откат: на 30 стр. меньше" in msg
    assert "Нажми «Продолжить» или введи другое число." in msg
    assert updates == []
    state = storage.get(user_id)
    assert state["state"] == "waiting_for_progress_confirm"
    assert state["data"]["pending_progress_page"] == 25


def test_confirm_applies_pending_value(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 2002
    storage = FakeStateStorage()
    updates = []
    save_progress_state(
        storage,
        user_id,
        state="waiting_for_progress_confirm",
        pending_progress_page=25,
    )
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(updates=updates))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())

    ctx = make_context(fake_api, user_id, "Продолжить", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "обновлён" in msg
    assert "Прогресс: 25/319 (8%)" in msg
    assert updates == [25]
    assert not storage.is_active(user_id)


def test_confirm_numeric_reentry_applies_when_not_suspicious(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 2003
    storage = FakeStateStorage()
    updates = []
    save_progress_state(
        storage,
        user_id,
        state="waiting_for_progress_confirm",
        pending_progress_page=25,
    )
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(updates=updates))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())

    ctx = make_context(fake_api, user_id, "65", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "обновлён" in msg
    assert "Прогресс: 65/319 (20%)" in msg
    assert updates == [65]
    assert not storage.is_active(user_id)


def test_confirm_numeric_reentry_reconfirms(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 2004
    storage = FakeStateStorage()
    updates = []
    save_progress_state(
        storage,
        user_id,
        state="waiting_for_progress_confirm",
        pending_progress_page=25,
    )
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(updates=updates))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())

    ctx = make_context(fake_api, user_id, "5", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "- Откат: на 50 стр. меньше" in msg
    assert updates == []
    state = storage.get(user_id)
    assert state["state"] == "waiting_for_progress_confirm"
    assert state["data"]["pending_progress_page"] == 5


def test_confirm_invalid_input_keeps_state(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 2005
    storage = FakeStateStorage()
    updates = []
    save_progress_state(
        storage,
        user_id,
        state="waiting_for_progress_confirm",
        pending_progress_page=25,
    )
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(updates=updates))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())

    ctx = make_context(fake_api, user_id, "abc", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert msg.startswith("⚠️ Не удалось обработать сообщение.")
    assert "Введи число" in msg
    assert updates == []
    state = storage.get(user_id)
    assert state["state"] == "waiting_for_progress_confirm"
    assert state["data"]["pending_progress_page"] == 25


def test_jump_by_speed_requires_confirmation(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 2006
    storage = FakeStateStorage()
    updates = []
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(updates=updates))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())

    ctx = make_context(fake_api, user_id, "300", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "- Скачок: +245 стр., больше обычного за неделю (2.89 стр/день)" in msg
    assert updates == []


def test_jump_without_history_uses_book_share(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 2007
    storage = FakeStateStorage()
    updates = []
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(updates=updates))
    monkeypatch.setattr(
        puf,
        "ReadingStatsService",
        make_stats_stub(weekly=0, monthly=0, avg=0, predicted=None),
    )

    ctx = make_context(fake_api, user_id, "300", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "- Скачок: +245 стр., больше 25% книги" in msg
    assert updates == []


def test_jump_floor_ignores_small_delta(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 2008
    storage = FakeStateStorage()
    updates = []
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(updates=updates))
    monkeypatch.setattr(
        puf,
        "ReadingStatsService",
        make_stats_stub(weekly=0, monthly=0, avg=0.5, predicted=None),
    )

    ctx = make_context(fake_api, user_id, "60", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "обновлён" in msg
    assert updates == [60]


def test_jump_floor_triggers_above_minimum(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 2009
    storage = FakeStateStorage()
    updates = []
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(updates=updates))
    monkeypatch.setattr(
        puf,
        "ReadingStatsService",
        make_stats_stub(weekly=0, monthly=0, avg=0.5, predicted=None),
    )

    ctx = make_context(fake_api, user_id, "70", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "- Скачок: +15 стр., больше обычного за неделю (0.50 стр/день)" in msg
    assert updates == []


def test_unchanged_progress_shows_notice(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 2010
    storage = FakeStateStorage()
    updates = []
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(updates=updates))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())

    ctx = make_context(fake_api, user_id, "55", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "ℹ️ Прогресс не изменился: 55/319 (17%)." in msg
    assert "За неделю прочитано: 20 стр." in msg
    assert updates == []
    assert not storage.is_active(user_id)


def test_progress_update_shows_goal_line(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 3000
    storage = FakeStateStorage()
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(user_id="user-1"))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())
    monkeypatch.setattr(puf, "GoalService", make_goal_stub(target=50, pages_today=35))

    ctx = make_context(fake_api, user_id, "60", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "Цель на день: 35/50 стр." in msg
    assert "🎉" not in msg


def test_progress_update_congratulates_on_goal_completion(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 3001
    storage = FakeStateStorage()
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(user_id="user-1"))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())
    monkeypatch.setattr(puf, "GoalService", make_goal_stub(target=50, pages_today=52))

    ctx = make_context(fake_api, user_id, "60", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "🎉 Цель на день выполнена! Сегодня прочитано 52 из 50 страниц." in msg
    assert "Цель на день: 52/50 стр." not in msg


def test_progress_update_without_goal_has_no_goal_line(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 3002
    storage = FakeStateStorage()
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(user_id="user-1"))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())
    monkeypatch.setattr(puf, "GoalService", make_goal_stub(target=None))

    ctx = make_context(fake_api, user_id, "60", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "Цель на день" not in msg
    assert "🎉" not in msg


def test_progress_update_does_not_repeat_congratulation(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 3003
    storage = FakeStateStorage()
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(user_id="user-1"))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())
    monkeypatch.setattr(puf, "GoalService", make_goal_stub(target=50, pages_today=60))

    ctx = make_context(fake_api, user_id, "60", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "Цель на день: 60/50 стр." in msg
    assert "🎉" not in msg


def test_unchanged_progress_does_not_congratulate(monkeypatch):
    fake_api = FakeVkApiMethod()
    user_id = 3004
    storage = FakeStateStorage()
    save_progress_state(storage, user_id)
    monkeypatch.setattr(puf, "BookService", make_progress_book_service(user_id="user-1"))
    monkeypatch.setattr(puf, "ReadingStatsService", make_stats_stub())
    monkeypatch.setattr(puf, "GoalService", make_goal_stub(target=50, pages_today=50))

    ctx = make_context(fake_api, user_id, "55", storage=storage)
    puf.ProgressUpdateFlow().handle(ctx)

    msg = fake_api.sent_messages[-1]["message"]
    assert "Цель на день: 50/50 стр." in msg
    assert "🎉" not in msg
