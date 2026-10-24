"""Тесты механизма цепочки промежуточных сообщений (issue #44).

Проверяют, что бот удаляет из чата свои промежуточные сообщения (промпты,
ошибки валидации) при отправке следующего, а финальные сообщения остаются.
"""

import types
from unittest.mock import MagicMock

import pytest
from conftest import FakeStateStorage, FakeVkApi, make_context

from vk_bot import message_chain
from vk_bot.handlers.add import AddHandler
from vk_bot.handlers.cancel import CancelHandler


def make_add_book_service():
    class StubBookService:
        def create_book(self, **kwargs):
            return types.SimpleNamespace(title=kwargs["title"])

    return StubBookService()


class TestSendMessageChain:
    """Поведение BotContext.send_message с активным и неактивным стейтом."""

    def test_first_send_without_state_no_delete_and_no_tracking(self):
        api = FakeVkApi()
        storage = FakeStateStorage()
        ctx = make_context(api, 1, "привет", storage=storage)

        ctx.send_message("Привет!")

        assert api.deleted_ids == []
        assert storage.get(1) == {}

    def test_send_in_active_state_tracks_message_id(self):
        api = FakeVkApi()
        storage = FakeStateStorage()
        storage.save(1, {"command": "/add", "state": "choose_method", "data": {}})
        ctx = make_context(api, 1, "Ручное", storage=storage)

        ctx.send_message("Введи название")

        assert api.deleted_ids == []
        assert storage.get(1)["data"][message_chain.LAST_MESSAGE_KEY] == 1

    def test_next_send_deletes_previous_intermediate(self):
        api = FakeVkApi()
        storage = FakeStateStorage()
        storage.save(1, {"command": "/add", "state": "choose_method", "data": {}})
        ctx = make_context(api, 1, "Ручное", storage=storage)

        ctx.send_message("Промпт 1")
        ctx.send_message("Промпт 2")
        ctx.send_message("Промпт 3")

        assert api.deleted_ids == [1, 2]
        assert storage.get(1)["data"][message_chain.LAST_MESSAGE_KEY] == 3

    def test_final_send_then_delete_state_keeps_final_message(self):
        api = FakeVkApi()
        storage = FakeStateStorage()
        storage.save(1, {"command": "/add", "state": "waiting_for_title", "data": {}})
        ctx = make_context(api, 1, "Мастер и Маргарита", storage=storage)

        ctx.send_message("Промпт")  # id 1, отслеживается
        ctx.send_message("Финал")  # id 2, удалит id 1, тоже в стейте
        ctx.delete_state()

        # После закрытия сценария следующее сообщение не удаляет финал.
        ctx2 = make_context(api, 1, "что-то", storage=storage)
        ctx2.send_message("Новая команда")

        assert api.deleted_ids == [1]
        assert ctx2.get_state() == {}

    def test_delete_error_is_swallowed(self):
        api = FakeVkApi()
        storage = FakeStateStorage()
        storage.save(1, {"command": "/add", "state": "choose_method", "data": {}})
        ctx = make_context(api, 1, "text", storage=storage)

        ctx.send_message("Промпт 1")

        def boom(**kwargs):
            raise RuntimeError("message too old")

        api.delete = boom
        ctx.send_message("Промпт 2")

        # Сообщение отправлено, сценарий не сломан, новый id запомнен.
        assert len(api.sent_messages) == 2
        assert storage.get(1)["data"][message_chain.LAST_MESSAGE_KEY] == 2

    def test_set_state_preserves_fresh_message_id_over_stale_dict(self):
        api = FakeVkApi()
        storage = FakeStateStorage()
        state = {"command": "/add", "state": "choose_method", "data": {}}
        storage.save(1, state)
        ctx = make_context(api, 1, "text", storage=storage)

        ctx.send_message("Промпт 1")  # storage: last_message_id = 1
        stale = ctx.get_state()  # снимок с id=1
        ctx.send_message("Промпт 2")  # storage: last_message_id = 2

        ctx.set_state(stale)  # локальный dict с устаревшим id=1

        assert storage.get(1)["data"][message_chain.LAST_MESSAGE_KEY] == 2

    def test_no_storage_is_safe(self):
        api = FakeVkApi()
        # storage=None: контекст вне хранилища стейта (как в /export-тесте).
        vk = MagicMock()
        vk.get_api.return_value = api
        event = MagicMock()
        event.user_id = 1
        event.peer_id = 1
        event.text = "text"
        event.payload = None
        from vk_bot.context import BotContext

        ctx = BotContext(vk=vk, upload=MagicMock(), event=event, storage=None)

        ctx.send_message("Привет!")
        ctx.send_message("Привет 2!")

        assert api.deleted_ids == []
        assert len(api.sent_messages) == 2

    def test_keyboard_and_attachment_passed_to_api(self):
        from vk_bot.keyboards import cancel_keyboard

        api = FakeVkApi()
        ctx = make_context(api, 1, "text", storage=None)

        ctx.send_message("Есть файл", attachment="doc10_20")
        ctx.send_message("С клавиатурой", keyboard=cancel_keyboard())

        assert api.sent_messages[0]["attachment"] == "doc10_20"
        assert "keyboard" not in api.sent_messages[0]
        assert api.sent_messages[1]["keyboard"] == cancel_keyboard().get_keyboard()


class TestCancelDeletesPrompt:
    def test_cancel_deletes_pending_prompt(self):
        api = FakeVkApi()
        storage = FakeStateStorage()
        storage.save(
            1,
            {
                "command": "/add",
                "state": "waiting_for_title",
                "data": {message_chain.LAST_MESSAGE_KEY: 42},
            },
        )
        ctx = make_context(api, 1, "/cancel", storage=storage)

        CancelHandler().handle(ctx)

        assert api.deleted_ids == [42]
        assert not storage.is_active(1)
        # Финал "Операция отменена" не отслеживается после delete_state.
        ctx2 = make_context(api, 1, "/start", storage=storage)
        ctx2.send_message("Привет!")
        assert api.deleted_ids == [42]


class TestAddScenarioChain:
    """Сквозная проверка цепочки в ручном добавлении книги."""

    @pytest.fixture(autouse=True)
    def patch_book_service(self, monkeypatch):
        monkeypatch.setattr("vk_bot.handlers.add.BookService", make_add_book_service)

    def test_manual_add_deletes_every_prompt_and_keeps_final(self):
        api = FakeVkApi()
        storage = FakeStateStorage()
        steps = ["/add", "Ручное", "Мастер и Маргарита", "Булгаков", "300", "Дальше", "Классика"]

        for text in steps:
            ctx = make_context(api, 7, text, storage=storage)
            AddHandler().handle(ctx)

        # 7 сообщений: prompt1 id1..prompt6 id6, финал id7.
        assert len(api.sent_messages) == 7
        # Каждое следующее удаляло предыдущее; финал не удалён.
        assert api.deleted_ids == [1, 2, 3, 4, 5, 6]
        assert not storage.is_active(7)

        # Следующая команда не трогает финальное сообщение.
        ctx = make_context(api, 7, "/list", storage=storage)
        ctx.send_message(
            "Список",
        )
        assert api.deleted_ids == [1, 2, 3, 4, 5, 6]
