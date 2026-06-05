"""List command handler as AbstractCommandHandler subclass.

Provides routing compatibility for the existing ``list.py`` implementation.
"""

from typing import Any

from vk_api.vk_api import VkApiMethod

from .base import AbstractCommandHandler
from .list import handle_list_command, handle_list_command_step


class ListHandler(AbstractCommandHandler):
    """Handler for the `/list` command.

    Supports entry point and step processing (pagination, etc.) using the
    ``active_states`` mechanism present in ``list.py``.
    """

    priority = 10
    commands = ["/list", "list"]

    def handle(self, api: VkApiMethod, user_id: int, *args: Any, **kwargs: Any):
        text = args[0] if args else None
        from vk_bot.states import active_states

        if user_id in active_states and active_states[user_id].get("command") == "/list":
            # Continue list flow – original handler expects ``event.text`` and payload
            payload = kwargs.get("payload")
            handle_list_command_step(api, user_id, text or "", payload)
        else:
            # Start list flow
            handle_list_command(api, user_id)
        return True
