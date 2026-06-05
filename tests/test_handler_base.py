import pytest
from unittest.mock import patch, MagicMock

from vk_bot.handlers.base import AbstractCommandHandler


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
    from vk_bot.handlers.add_handler import AddHandler

    handler = AddHandler()
    assert "/add" in handler.commands
    assert "add" in handler.commands
    assert handler.priority == 10


def test_edit_handler_commands():
    from vk_bot.handlers.edit_handler import EditHandler

    handler = EditHandler()
    assert "/edit" in handler.commands
    assert "edit" in handler.commands
    assert handler.can_handle("/edit") is True
    assert handler.can_handle("edit") is True


def test_list_handler_commands():
    from vk_bot.handlers.list_handler import ListHandler

    handler = ListHandler()
    assert "/list" in handler.commands
    assert "list" in handler.commands
    assert handler.can_handle("/list") is True


def test_details_handler_commands():
    from vk_bot.handlers.details_handler import DetailsHandler

    handler = DetailsHandler()
    assert "/details" in handler.commands
    assert "details" in handler.commands
    assert handler.can_handle("/details") is True


def test_add_handler_handle_returns_true():
    from vk_bot.handlers.add_handler import AddHandler

    handler = AddHandler()
    fake_context = make_fake_context()

    with patch("vk_bot.handlers.add_handler.handle_add_command") as mock_cmd:
        result = handler.handle(fake_context)
        assert result is True
        mock_cmd.assert_called_once_with(fake_context)


def test_edit_handler_handle_returns_true():
    from vk_bot.handlers.edit_handler import EditHandler

    handler = EditHandler()
    fake_context = make_fake_context()

    with patch("vk_bot.handlers.edit_handler.handle_edit_command") as mock_cmd:
        result = handler.handle(fake_context)
        assert result is True
        mock_cmd.assert_called_once_with(fake_context)


def test_list_handler_handle_returns_true():
    from vk_bot.handlers.list_handler import ListHandler

    handler = ListHandler()
    fake_context = make_fake_context()

    with patch("vk_bot.handlers.list_handler.handle_list_command") as mock_cmd:
        result = handler.handle(fake_context)
        assert result is True
        mock_cmd.assert_called_once_with(fake_context)


def test_details_handler_handle_returns_true():
    from vk_bot.handlers.details_handler import DetailsHandler

    handler = DetailsHandler()
    fake_context = make_fake_context()

    with patch("vk_bot.handlers.details_handler.handle_details") as mock_cmd:
        result = handler.handle(fake_context)
        assert result is True
        mock_cmd.assert_called_once_with(fake_context)
