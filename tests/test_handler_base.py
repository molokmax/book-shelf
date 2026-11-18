from unittest.mock import MagicMock, patch

import pytest

from vk_bot.handlers.base import FOREIGN_SCENARIO_MESSAGE, AbstractCommandHandler


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

    def get_current_state(self, user_id):
        state = self._data.get(user_id)
        return state.get("state") if state else None


def make_fake_context(user_id=999, text="/add", storage=None):
    vk = MagicMock()
    vk.get_api.return_value = MagicMock()
    upload = MagicMock()
    event = MagicMock()
    event.user_id = user_id
    event.peer_id = user_id
    event.text = text
    event.payload = None
    from vk_bot.context import BotContext

    return BotContext(vk=vk, upload=upload, event=event, storage=storage or FakeStateStorage())


def test_abstract_handler_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        AbstractCommandHandler()


def test_concrete_handler_provides_commands():
    from vk_bot.handlers.add import AddHandler

    handler = AddHandler()
    assert "/add" in handler.commands
    assert "add" in handler.commands
    assert handler.priority == 10


def test_edit_handler_commands():
    from vk_bot.handlers.edit import EditHandler

    handler = EditHandler()
    assert "/edit" in handler.commands
    assert "edit" in handler.commands
    assert handler.can_handle("/edit") is True
    assert handler.can_handle("edit") is True


def test_list_handler_commands():
    from vk_bot.handlers.list import ListHandler

    handler = ListHandler()
    assert "/list" in handler.commands
    assert "list" in handler.commands
    assert handler.can_handle("/list") is True


def test_details_handler_commands():
    from vk_bot.handlers.details import DetailsHandler

    handler = DetailsHandler()
    assert "/details" in handler.commands
    assert "details" in handler.commands
    assert handler.can_handle("/details") is True


def test_add_handler_handle_returns_true():
    from vk_bot.handlers.add import AddHandler

    handler = AddHandler()
    fake_context = make_fake_context()

    with patch.object(handler, "start") as mock_start:
        result = handler.handle(fake_context)
        assert result is True
        mock_start.assert_called_once_with(fake_context)


def test_edit_handler_handle_returns_true():
    from vk_bot.handlers.edit import EditHandler

    handler = EditHandler()
    fake_context = make_fake_context()

    with patch.object(handler, "start") as mock_entry:
        result = handler.handle(fake_context)
        assert result is True
        mock_entry.assert_called_once_with(fake_context)


def test_list_handler_handle_returns_true():
    from vk_bot.handlers.list import ListHandler

    handler = ListHandler()
    fake_context = make_fake_context()

    with patch.object(handler, "start") as mock_entry:
        result = handler.handle(fake_context)
        assert result is True
        mock_entry.assert_called_once_with(fake_context)


def test_details_handler_handle_returns_true():
    from vk_bot.handlers.details import DetailsHandler

    handler = DetailsHandler()
    fake_context = make_fake_context()

    with patch.object(handler, "start") as mock_entry:
        result = handler.handle(fake_context)
        assert result is True
        mock_entry.assert_called_once_with(fake_context)


# ── Гард чужого сценария ────────────────────────────────────────────


class StubHandler(AbstractCommandHandler):
    commands = ["/stub"]
    scenario_command = "/stub"

    def _handle(self, context):
        return "handled"


class SystemStubHandler(StubHandler):
    commands = ["/system"]
    scenario_command = "/system"
    is_system = True


class StatelessStubHandler(AbstractCommandHandler):
    commands = ["/stateless"]

    def _handle(self, context):
        return "stateless handled"


def make_state_context(command, state_command, text=None):
    storage = FakeStateStorage()
    if state_command is not None:
        storage.save(
            1,
            {"command": state_command, "state": "waiting_for_title", "data": {"a": 1}},
        )
    context = make_fake_context(user_id=1, text=text or command, storage=storage)
    return context, storage


def test_foreign_scenario_rejects_command():
    context, storage = make_state_context("/stub", "/add")

    result = StubHandler().handle(context)

    assert result is True
    context.api.messages.send.assert_called_once()
    assert context.api.messages.send.call_args.kwargs["message"] == FOREIGN_SCENARIO_MESSAGE
    assert storage.get(1) == {
        "command": "/add",
        "state": "waiting_for_title",
        "data": {"a": 1},
    }


def test_own_scenario_is_handled():
    context, storage = make_state_context("/stub", "/stub")

    result = StubHandler().handle(context)

    assert result == "handled"
    context.api.messages.send.assert_not_called()


def test_stateless_command_is_blocked_by_foreign_scenario():
    context, _ = make_state_context("/stateless", "/add")

    result = StatelessStubHandler().handle(context)

    assert result is True
    context.api.messages.send.assert_called_once()
    assert context.api.messages.send.call_args.kwargs["message"] == FOREIGN_SCENARIO_MESSAGE


def test_system_command_ignores_foreign_scenario():
    context, _ = make_state_context("/system", "/add")

    result = SystemStubHandler().handle(context)

    assert result == "handled"
    context.api.messages.send.assert_not_called()


def test_state_without_owner_is_not_blocked():
    context, storage = make_state_context("/stub", None)
    storage.save(1, {"command": "", "state": "menu", "data": {}})

    result = StubHandler().handle(context)

    assert result == "handled"
    context.api.messages.send.assert_not_called()
