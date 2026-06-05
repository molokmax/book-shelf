"""List command handler as AbstractCommandHandler subclass.

Provides routing compatibility for the existing ``list.py`` implementation.
"""

from typing import Any

from ..context import BotContext
from .base import AbstractCommandHandler
from .list import handle_list_command, handle_list_command_step


class ListHandler(AbstractCommandHandler):
    """Handler for the `/list` command.

    Supports entry point and step processing (pagination, etc.) using the
    ``active_states`` mechanism present in ``list.py``.
    """

    priority = 10
    commands = ["/list", "list"]

    def handle(self, context: BotContext) -> Any:
        if context.is_active() and context.command_state == "/list":
            handle_list_command_step(context)
        else:
            handle_list_command(context)
        return True
