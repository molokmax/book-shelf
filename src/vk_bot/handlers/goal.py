"""Обработчик команды /goal: дневная цель чтения."""

from typing import Any

from vk_api.keyboard import VkKeyboard

from core.services import GoalService
from utils import helpers
from vk_bot.keyboards import cancel_keyboard, main_keyboard
from vk_bot.user_helpers import get_or_create_user

from ..context import BotContext
from .base import AbstractCommandHandler


class GoalHandler(AbstractCommandHandler):
    """Handler for the `/goal` command.

    Управляет состояниями:
    * menu: выбор действия (просмотр, установка, отключение)
    * waiting_for_goal_input: ввод количества страниц в день
    """

    priority = 10
    commands = ["/goal", "goal", "цель"]

    def handle(self, context: BotContext) -> Any:
        state_info = context.get_state()

        # Не перехватываем управление у активного сценария другой команды.
        if context.is_active() and state_info.get("command") != "/goal":
            return None

        if not context.is_active():
            self._handle_entry(context)
            return True

        state = state_info.get("state")
        if state == "menu":
            self._handle_menu(context, state_info)
        elif state == "waiting_for_goal_input":
            self._handle_input(context, state_info)

        return True

    def _handle_entry(self, context: BotContext) -> None:
        user = get_or_create_user(context.api, context.user_id)
        context.set_state(
            {
                "command": "/goal",
                "state": "menu",
                "data": {"user_id": user.id},
            }
        )
        context.send_message(
            "Цель на день\n\nВыбери действие:",
            keyboard=self._create_menu_keyboard(),
        )

    def _handle_menu(self, context: BotContext, state_info: dict) -> None:
        choice = context.text.strip().lower()
        if choice == "просмотр":
            self._show_status(context, state_info)
        elif choice == "установить":
            self._start_set(context, state_info)
        elif choice == "отключить":
            self._disable(context, state_info)
        else:
            context.send_message(
                helpers.format_invalid_input("Выбери действие из клавиатуры."),
                keyboard=self._create_menu_keyboard(),
            )

    def _show_status(self, context: BotContext, state_info: dict) -> None:
        service = GoalService()
        status = service.get_goal_status(self._user_id(context, state_info))
        if status is None:
            self._finish(
                context,
                "Цель на день не установлена.\n\n"
                "Нажми «Установить», чтобы задать количество страниц в день.",
            )
            return

        lines = [
            f"Цель на день: {status.goal.target} стр.",
            f"Сегодня прочитано: {status.pages_today} стр. ({status.percent}%)",
        ]
        if status.completed:
            lines.append("Цель выполнена.")
        else:
            lines.append(f"Осталось: {status.remaining} стр.")
        self._finish(context, "\n".join(lines))

    def _start_set(self, context: BotContext, state_info: dict) -> None:
        state_info["state"] = "waiting_for_goal_input"
        context.set_state(state_info)
        context.send_message(
            "Введи количество страниц в день (целое число).\n\n0 — отключить цель.",
            keyboard=cancel_keyboard(),
        )

    def _handle_input(self, context: BotContext, state_info: dict) -> None:
        try:
            value = int(context.text.strip())
        except ValueError:
            context.send_message(
                helpers.format_invalid_input("Введи целое число, например 20."),
                keyboard=cancel_keyboard(),
            )
            return

        if value < 0:
            context.send_message(
                helpers.format_invalid_input("Цель не может быть отрицательной."),
                keyboard=cancel_keyboard(),
            )
            return

        service = GoalService()
        user_id = self._user_id(context, state_info)
        if value == 0:
            service.disable_goal(user_id)
            self._finish(context, "Цель отключена.")
            return

        service.set_daily_goal(user_id, value)
        self._finish(context, f"Цель на день установлена: {value} стр.")

    def _disable(self, context: BotContext, state_info: dict) -> None:
        service = GoalService()
        if not service.disable_goal(self._user_id(context, state_info)):
            self._finish(context, "Цель не установлена.")
            return
        self._finish(context, "Цель отключена.")

    @staticmethod
    def _user_id(context: BotContext, state_info: dict) -> str:
        user_id = state_info.get("data", {}).get("user_id")
        if not user_id:
            user = get_or_create_user(context.api, context.user_id)
            user_id = user.id
            state_info.setdefault("data", {})["user_id"] = user_id
            context.set_state(state_info)
        return user_id

    def _finish(self, context: BotContext, message: str) -> None:
        # Финал: отправляем до delete_state, чтобы удалить висящий промпт.
        context.send_message(message, keyboard=main_keyboard())
        context.delete_state()

    @staticmethod
    def _create_menu_keyboard() -> VkKeyboard:
        """Клавиатура меню целей."""
        kb = VkKeyboard()
        kb.add_button("Просмотр")
        kb.add_button("Установить")
        kb.add_line()
        kb.add_button("Отключить")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb
