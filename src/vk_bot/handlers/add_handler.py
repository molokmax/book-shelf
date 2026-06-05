"""Add command handler as AbstractCommandHandler subclass.

This wrapper allows the new routing system to use the existing implementation
without rewriting the whole state‑machine logic.
"""

from typing import Any

from vk_api.vk_api import VkApiMethod

from .base import AbstractCommandHandler
from .add import handle_add_command, handle_add_command_step


class AddHandler(AbstractCommandHandler):
    """Handler for the `/add` command.

    The command has two phases:
    1. Entry point – when the command is received without an active state.
    2. Step processing – when the user is already in the add flow (state stored
       in ``vk_bot.states.active_states``).
    """

    priority = 10
    commands = ["/add", "add"]

    def handle(self, api: VkApiMethod, user_id: int, *args: Any, **kwargs: Any):
        # ``args`` may contain the message text when we are in a step.
        text = args[0] if args else None
        # If the user already has a state for this command, delegate to the step
        # handler; otherwise start the command.
        from vk_bot.states import active_states

        if user_id in active_states and active_states[user_id].get("command") == "/add":
            # Step handling – ``text`` is the incoming message.
            handle_add_command_step(api, user_id, text or "")
        else:
            # Entry point – start the add flow.
            handle_add_command(api, user_id)
        # Indicate that the command was handled
        return True
