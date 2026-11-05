"""Обработчик команды /settings: персональные настройки бота."""

from typing import Any

from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

from core.models import READING_SPEED_PERIODS
from core.services import UserSettingsService
from utils import helpers
from vk_bot.keyboards import main_keyboard
from vk_bot.user_helpers import get_or_create_user

from ..context import BotContext
from .base import AbstractCommandHandler


class SettingsHandler(AbstractCommandHandler):
    """Handler for the `/settings` command.

    Управляет состояниями:
    * menu: просмотр настроек, изменение периода скорости чтения и тоггл мотивации
    """

    priority = 10
    commands = ["/settings"]

    def handle(self, context: BotContext) -> Any:
        state_info = context.get_state()

        # Не перехватываем управление у активного сценария другой команды.
        if context.is_active() and state_info.get("command") != "/settings":
            return None

        if not context.is_active():
            self._handle_entry(context)
            return True

        state = state_info.get("state")
        if state == "menu":
            self._handle_menu(context, state_info)
        return True

    def _handle_entry(self, context: BotContext) -> None:
        """Открывает экран настроек с текущими значениями."""
        user = get_or_create_user(context.api, context.user_id)
        context.set_state(
            {
                "command": "/settings",
                "state": "menu",
                "data": {"user_id": user.id},
            }
        )
        service = UserSettingsService()
        motivation_enabled = service.is_motivation_enabled(user.id)
        message = self._format_settings_screen(
            service.get_reading_speed_period(user.id), motivation_enabled
        )
        self._send(context, message, self._create_settings_keyboard(motivation_enabled))

    def _handle_menu(self, context: BotContext, state_info: dict) -> None:
        choice = context.text.strip().lower()

        if choice == "назад":
            self._handle_back(context)
            return

        user_id = self._user_id(context, state_info)

        # Метка кнопки-переключателя отражает текущее состояние, тап инвертирует.
        if choice in ("мотивация: вкл", "мотивация: выкл"):
            self._handle_motivation_toggle(context, user_id)
            return

        # Метки кнопок строятся из константы доступных периодов.
        periods = {f"{days} дней": days for days in READING_SPEED_PERIODS}
        new_period = periods.get(choice)
        if new_period is None:
            self._send(
                context,
                helpers.format_invalid_input("Выбери значение из клавиатуры."),
                self._create_settings_keyboard(
                    UserSettingsService().is_motivation_enabled(user_id)
                ),
            )
            return

        service = UserSettingsService()
        service.set_reading_speed_period(user_id, new_period)
        self._send(
            context,
            f"Период скорости чтения: {new_period} дней",
            self._create_settings_keyboard(service.is_motivation_enabled(user_id)),
        )

    def _handle_motivation_toggle(self, context: BotContext, user_id: str) -> None:
        """Инвертирует настройку мотивации и подтверждает новое состояние."""
        service = UserSettingsService()
        enabled = service.is_motivation_enabled(user_id)
        service.set_motivation_enabled(user_id, not enabled)

        self._send(
            context,
            "Мотивация включена" if not enabled else "Мотивация выключена",
            self._create_settings_keyboard(not enabled),
        )

    def _handle_back(self, context: BotContext) -> None:
        """Выходит из настроек в главное меню."""
        context.delete_state()
        self._send(context, "Возврат в главное меню", main_keyboard())

    @staticmethod
    def _format_settings_screen(period_days: int, motivation_enabled: bool) -> str:
        """Экран настроек со значениями всех настроек."""
        motivation_state = "включена" if motivation_enabled else "выключена"
        return (
            "Настройки\n\n"
            f"Период скорости чтения: {period_days} дней\n"
            "(за сколько дней считается среднее количество страниц в день)\n\n"
            f"Мотивация: {motivation_state}\n"
            "(подбадривающая фраза после обновления прогресса)"
        )

    @staticmethod
    def _user_id(context: BotContext, state_info: dict) -> str:
        user_id = state_info.get("data", {}).get("user_id")
        if not user_id:
            user = get_or_create_user(context.api, context.user_id)
            user_id = user.id
            state_info.setdefault("data", {})["user_id"] = user_id
            context.set_state(state_info)
        return user_id

    @staticmethod
    def _create_settings_keyboard(motivation_enabled: bool) -> VkKeyboard:
        """Клавиатура экрана настроек.

        Тоггл мотивации: метка показывает текущее состояние, цвет
        подсвечивает включённую мотивацию (по образцу переключателей тегов).
        """
        kb = VkKeyboard()
        kb.add_button("7 дней")
        kb.add_button("14 дней")
        kb.add_line()
        kb.add_button("30 дней")
        kb.add_button(
            "Мотивация: Вкл" if motivation_enabled else "Мотивация: Выкл",
            color=(VkKeyboardColor.PRIMARY if motivation_enabled else VkKeyboardColor.SECONDARY),
        )
        kb.add_line()
        kb.add_button("Назад")
        return kb

    @staticmethod
    def _send(context: BotContext, message: str, keyboard: VkKeyboard) -> None:
        context.api.messages.send(
            user_id=context.user_id,
            message=message,
            keyboard=keyboard.get_keyboard(),
            random_id=get_random_id(),
        )
