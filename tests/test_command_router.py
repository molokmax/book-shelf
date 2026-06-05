from unittest.mock import MagicMock, patch

with patch(
    "utils.config.load_config",
    return_value=type(
        "Config", (), {"BOT_TOKEN": "dummy", "data_dir": "data"}
    ),
):
    from vk_bot.command_router import CommandRouter

from vk_bot.handlers.base import AbstractCommandHandler


def make_context(command="/add"):
    vk = MagicMock()
    vk.get_api.return_value = MagicMock()
    upload = MagicMock()
    event = MagicMock()
    event.user_id = 1
    event.peer_id = 1
    event.text = command
    event.payload = None
    from vk_bot.context import BotContext

    return BotContext(vk=vk, upload=upload, event=event)


class HandlerA(AbstractCommandHandler):
    priority = 10
    commands = ["/add", "add"]

    def handle(self, context):
        return "HandlerA handled"


class HandlerB(AbstractCommandHandler):
    priority = 20
    commands = ["/add", "add"]

    def handle(self, context):
        return "HandlerB handled"


class HandlerC(AbstractCommandHandler):
    priority = 5
    commands = ["/list"]

    def handle(self, context):
        return "HandlerC handled"


class HandlerNeverMatches(AbstractCommandHandler):
    priority = 0
    commands = []

    def handle(self, context):
        return "Should not be called"


def test_route_selects_highest_priority_handler():
    router = CommandRouter()
    router.register_handler(HandlerA())
    router.register_handler(HandlerB())

    result = router.route(make_context(command="/add"))

    assert result == "HandlerB handled"


def test_route_selects_correct_handler_by_command():
    router = CommandRouter()
    router.register_handler(HandlerA())
    router.register_handler(HandlerC())

    result = router.route(make_context(command="/list"))

    assert result == "HandlerC handled"


def test_route_returns_none_when_no_handler_matches():
    router = CommandRouter()
    router.register_handler(HandlerA())
    router.register_handler(HandlerC())

    result = router.route(make_context(command="/unknown"))

    assert result is None


def test_route_continues_on_error():
    router = CommandRouter()

    class BrokenHandler(AbstractCommandHandler):
        priority = 20
        commands = ["/broken"]

        def handle(self, context):
            raise RuntimeError("Something went wrong")

    router.register_handler(BrokenHandler())
    router.register_handler(HandlerC())

    result = router.route(make_context(command="/list"))

    assert result == "HandlerC handled"


def test_handlers_sorted_by_priority_descending():
    router = CommandRouter()
    router.register_handler(HandlerA())
    router.register_handler(HandlerB())
    router.register_handler(HandlerC())

    assert router.handlers[0].priority == 20
    assert router.handlers[1].priority == 10
    assert router.handlers[2].priority == 5


def test_register_handler_logs_debug():
    router = CommandRouter()
    with patch.object(router.logger, "debug") as mock_debug:
        router.register_handler(HandlerA())
        mock_debug.assert_called_once()


def test_can_handle_returns_true_for_registered_command():
    handler = HandlerA()

    assert handler.can_handle("/add") is True
    assert handler.can_handle("add") is True


def test_can_handle_returns_false_for_unknown_command():
    handler = HandlerA()

    assert handler.can_handle("/unknown") is False
