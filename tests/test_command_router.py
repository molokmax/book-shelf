from unittest.mock import MagicMock, patch

with patch(
    "utils.config.load_config",
    return_value=type("Config", (), {"BOT_TOKEN": "dummy", "data_dir": "data"}),
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


# -----------------------------------------------------------------------
# Тесты для роутинга по активному стейту (state-based-routing)
# -----------------------------------------------------------------------


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


def make_context_with_state(command="/add", state_command=None):
    """Создаёт BotContext с возможностью указать активный стейт."""
    storage = FakeStateStorage()
    if state_command:
        storage.save(1, {"command": state_command, "state": "waiting", "data": {}})

    vk = MagicMock()
    vk.get_api.return_value = MagicMock()
    upload = MagicMock()
    event = MagicMock()
    event.user_id = 1
    event.peer_id = 1
    event.text = command
    event.payload = None
    from vk_bot.context import BotContext

    return BotContext(vk=vk, upload=upload, event=event, storage=storage)


def test_route_by_active_state_when_no_command_match():
    """Если ни один обработчик не совпал по введённой команде,
    но есть активный стейт — роутинг идёт по команде из стейта."""
    router = CommandRouter()
    router.register_handler(HandlerA())  # /add, priority 10
    router.register_handler(HandlerC())  # /list, priority 5

    ctx = make_context_with_state(command="просто текст", state_command="/add")
    result = router.route(ctx)

    assert result == "HandlerA handled"


def test_route_high_priority_intercepts_before_state_check():
    """Обработчик с высоким приоритетом должен перехватить сообщение
    до того, как начнётся поиск по стейту."""
    router = CommandRouter()
    router.register_handler(HandlerA())  # /add, priority 10

    class CancelLikeHandler(AbstractCommandHandler):
        priority = 100
        commands = ["отмена"]

        def handle(self, context):
            return "CancelLikeHandler handled"

    router.register_handler(CancelLikeHandler())

    ctx = make_context_with_state(command="отмена", state_command="/add")
    result = router.route(ctx)

    assert result == "CancelLikeHandler handled"


def test_route_state_based_preserves_priority():
    """При поиске по стейту выбирается обработчик с наивысшим приоритетом."""
    router = CommandRouter()
    router.register_handler(HandlerA())  # /add, priority 10
    router.register_handler(HandlerB())  # /add, priority 20

    ctx = make_context_with_state(command="просто текст", state_command="/add")
    result = router.route(ctx)

    assert result == "HandlerB handled"


def test_route_no_state_no_change():
    """Без активного стейта поведение не меняется —
    маршрутизация только по введённой команде."""
    router = CommandRouter()
    router.register_handler(HandlerA())
    router.register_handler(HandlerC())

    ctx = make_context_with_state(command="/list", state_command=None)
    result = router.route(ctx)

    assert result == "HandlerC handled"


def test_route_returns_none_when_state_command_has_no_handler():
    """Если есть активный стейт, но ни один обработчик
    не поддерживает команду из стейта — возвращается None."""
    router = CommandRouter()
    router.register_handler(HandlerA())  # /add, priority 10

    ctx = make_context_with_state(command="просто текст", state_command="/unknown")
    result = router.route(ctx)

    assert result is None
