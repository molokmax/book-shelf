"""Параметризованный гард: чужая команда не выполняется в активном сценарии."""

import pytest
from conftest import FakeStateStorage
from conftest import FakeVkApi as FakeVkApiMethod
from conftest import make_context

from vk_bot.handlers.add import AddHandler
from vk_bot.handlers.base import FOREIGN_SCENARIO_MESSAGE
from vk_bot.handlers.details import DetailsHandler
from vk_bot.handlers.edit import EditHandler
from vk_bot.handlers.export import ExportHandler
from vk_bot.handlers.goal import GoalHandler
from vk_bot.handlers.help import HelpHandler
from vk_bot.handlers.list import ListHandler
from vk_bot.handlers.more import MoreHandler
from vk_bot.handlers.progress import ProgressHandler
from vk_bot.handlers.settings import SettingsHandler
from vk_bot.handlers.stats import StatsHandler

FOREIGN_COMMANDS = [
    (HelpHandler(), "/add"),
    (StatsHandler(), "/add"),
    (ExportHandler(), "/add"),
    (MoreHandler(), "/add"),
    (AddHandler(), "/edit"),
    (EditHandler(), "/add"),
    (DetailsHandler(), "/add"),
    (ListHandler(), "/add"),
    (ProgressHandler(), "/add"),
    (GoalHandler(), "/add"),
    (SettingsHandler(), "/add"),
]


@pytest.mark.parametrize(
    "handler",
    [
        AddHandler(),
        EditHandler(),
        DetailsHandler(),
        ListHandler(),
        ProgressHandler(),
        GoalHandler(),
        SettingsHandler(),
    ],
    ids=lambda handler: handler.__class__.__name__,
)
def test_scenario_command_is_canonical(handler):
    """В state["command"] пишется первая (каноническая) команда сценария."""
    assert handler.scenario_command == handler.commands[0]
    assert handler.scenario_command.startswith("/")


@pytest.mark.parametrize(
    "handler, owner",
    FOREIGN_COMMANDS,
    ids=[handler.__class__.__name__ for handler, _ in FOREIGN_COMMANDS],
)
def test_command_is_rejected_during_foreign_scenario(handler, owner):
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    state = {"command": owner, "state": "some_step", "data": {"title": "Book"}}
    storage.save(1, state)

    result = handler.handle(make_context(fake_api, 1, "/whatever", storage=storage))

    assert result is True
    assert fake_api.sent_messages[-1]["message"] == FOREIGN_SCENARIO_MESSAGE
    assert storage.get(1) == state
