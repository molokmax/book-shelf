"""Add command handler as AbstractCommandHandler subclass.

This wrapper allows the new routing system to use the existing implementation
without rewriting the whole state‑machine logic.
"""

from typing import Any

from ..context import BotContext
from .add import handle_add_command, handle_add_command_step
from .base import AbstractCommandHandler


class AddHandler(AbstractCommandHandler):
    """Handler for the `/add` command.

    The command has two phases:
    1. Entry point – when the command is received without an active state.
    2. Step processing – when the user is already in the add flow (state stored
       in ``vk_bot.states.active_states``).
    """

    priority = 10
    commands = ["/add", "add"]

    def handle(self, context: BotContext) -> Any:
        from vk_bot.states import active_states

        if (
            context.user_id in active_states
            and active_states[context.user_id].get("command") == "/add"
        ):
            handle_add_command_step(context)
        else:
            handle_add_command(context)
        return True
