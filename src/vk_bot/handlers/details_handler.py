"""Details command handler as AbstractCommandHandler subclass.

Provides routing compatibility for the existing ``details.py`` implementation.
"""

from typing import Any

from vk_api.vk_api import VkApiMethod

from .base import AbstractCommandHandler
from .details import handle_details, handle_details_step


class DetailsHandler(AbstractCommandHandler):
    """Handler for the `/details` command.

    Mirrors the two‑phase flow of the original implementation:
    * Entry point – ``handle_details``
    * Subsequent steps – ``handle_details_step``
    """

    priority = 10
    commands = ["/details", "details"]

    def handle(self, api: VkApiMethod, user_id: int, *args: Any, **kwargs: Any):
        text = args[0] if args else None
        from vk_bot.states import active_states

        if user_id in active_states and active_states[user_id].get("command") == "/details":
            # Continue details flow – original handler expects text and payload
            payload = kwargs.get("payload")
            handle_details_step(api, user_id, text or "", payload)
        else:
            # Start details flow
            handle_details(api, user_id)
        return True
