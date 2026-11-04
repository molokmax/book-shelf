"""Обработчик навигации: подменю «Ещё» и возврат в главное меню."""

from typing import Any

from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id

from vk_bot.keyboards import main_keyboard, more_keyboard

from ..context import BotContext
from .base import AbstractCommandHandler


class MoreHandler(AbstractCommandHandler):
    """Навигация по меню: открытие подменю «Ещё» и возврат в главное меню.

    Работает без состояния в ``user_state``: это навигация по клавиатуре,
    а не сценарий с диалогом. Маршрутизация по payload: кнопка «Ещё» несёт
    ``{"command": "/more"}``, кнопка «Назад» несёт ``{"command": "/back"}``.
    """

    priority = 10
    commands = ["/more", "/back"]

    def handle(self, context: BotContext) -> Any:
        # Не перехватываем управление у активного сценария другой команды.
        if context.is_active() and context.command_state not in self.commands:
            return None

        if context.command == "/back":
            self._show_main_menu(context)
        else:
            self._show_more(context)
        return True

    # ---------------------------------------------------------------------
    # Экраны
    # ---------------------------------------------------------------------
    def _show_more(self, context: BotContext) -> None:
        """Экран «Ещё» со списком остальных команд."""
        message = (
            "Ещё\n\n"
            "/edit - Редактировать книгу\n"
            "/export - Экспорт списка книг в CSV\n"
            "/goal - Дневная цель чтения\n"
            "/stats - Статистика чтения\n"
            "/settings - Настройки приложения"
        )
        self._send(context, message, more_keyboard())

    def _show_main_menu(self, context: BotContext) -> None:
        """Возврат в главное меню."""
        self._send(context, "Главное меню", main_keyboard())

    @staticmethod
    def _send(context: BotContext, message: str, keyboard: VkKeyboard) -> None:
        context.api.messages.send(
            user_id=context.user_id,
            message=message,
            keyboard=keyboard.get_keyboard(),
            random_id=get_random_id(),
        )
