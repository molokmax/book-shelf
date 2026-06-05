"""Edit command handler as AbstractCommandHandler subclass.

Wraps the existing `edit.py` step‑wise implementation so the new routing system can
use it without rewriting the internal state machine.
"""

from typing import Any

from ..context import BotContext
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

    def handle(self, context: BotContext) -> Any:
        if context.is_active() and context.command_state == "/edit":
            handle_edit_command_step(context)
        else:
            handle_edit_command(context)
        return True
