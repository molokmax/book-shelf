import pytest
from unittest.mock import patch, MagicMock

from vk_bot.handlers.base import AbstractCommandHandler


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
    from vk_bot.states import active_states

    active_states.clear()
    handler = AddHandler()
    fake_api = MagicMock()

    with patch("vk_bot.handlers.add_handler.handle_add_command") as mock_cmd:
        result = handler.handle(fake_api, 999)
        assert result is True
        mock_cmd.assert_called_once_with(fake_api, 999)


def test_edit_handler_handle_returns_true():
    from vk_bot.handlers.edit_handler import EditHandler
    from vk_bot.states import active_states

    active_states.clear()
    handler = EditHandler()
    fake_api = MagicMock()

    with patch("vk_bot.handlers.edit_handler.handle_edit_command") as mock_cmd:
        result = handler.handle(fake_api, 999)
        assert result is True
        mock_cmd.assert_called_once_with(fake_api, 999)


def test_list_handler_handle_returns_true():
    from vk_bot.handlers.list_handler import ListHandler
    from vk_bot.states import active_states

    active_states.clear()
    handler = ListHandler()
    fake_api = MagicMock()

    with patch("vk_bot.handlers.list_handler.handle_list_command") as mock_cmd:
        result = handler.handle(fake_api, 999)
        assert result is True
        mock_cmd.assert_called_once_with(fake_api, 999)


def test_details_handler_handle_returns_true():
    from vk_bot.handlers.details_handler import DetailsHandler
    from vk_bot.states import active_states

    active_states.clear()
    handler = DetailsHandler()
    fake_api = MagicMock()

    with patch("vk_bot.handlers.details_handler.handle_details") as mock_cmd:
        result = handler.handle(fake_api, 999)
        assert result is True
        mock_cmd.assert_called_once_with(fake_api, 999)
