"""Тесты справки по командам бота."""

from conftest import FakeVkApi as FakeVkApiMethod
from conftest import make_context

from vk_bot.handlers.help import HelpHandler


def test_help_contains_details_and_achievements():
    api = FakeVkApiMethod()

    result = HelpHandler().handle(make_context(api, 1, "/help"))

    assert result is True
    message = api.sent_messages[-1]["message"]
    assert "* /details - Полная информация о выбранной книге" in message
    assert "* /achievements - Каталог достижений" in message
