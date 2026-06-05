"""Edit command handler as AbstractCommandHandler subclass.

Wraps the existing `edit.py` step‑wise implementation so the new routing system can
use it without rewriting the internal state machine.
"""

from typing import Any

from vk_api.vk_api import VkApiMethod

from .base import AbstractCommandHandler
from .edit import handle_edit_command, handle_edit_command_step


class EditHandler(AbstractCommandHandler):
    """Handler for the `/edit` command.

    Mirrors the two‑phase flow of the original implementation:
    * Entry point – `handle_edit_command`
    * Subsequent steps – `handle_edit_command_step`
    """

    priority = 10
    commands = ["/edit", "edit"]

    def handle(self, api: VkApiMethod, user_id: int, *args: Any, **kwargs: Any):
        text = args[0] if args else None
        from vk_bot.states import active_states

        if user_id in active_states and active_states[user_id].get("command") == "/edit":
            # Continue edit flow
            handle_edit_command_step(api, user_id, text or "", kwargs.get("payload"))
        else:
            # Start edit flow
            handle_edit_command(api, user_id)
        return True
