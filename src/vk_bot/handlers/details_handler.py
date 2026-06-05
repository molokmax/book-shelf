"""Details command handler as AbstractCommandHandler subclass.

Provides routing compatibility for the existing ``details.py`` implementation.
"""

from typing import Any

from ..context import BotContext
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

    def handle(self, context: BotContext) -> Any:
        if context.is_active() and context.command_state == "/details":
            handle_details_step(context)
        else:
            handle_details(context)
        return True
