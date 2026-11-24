"""Обработчик команды /goal: дневная цель чтения."""

from typing import Any

from vk_api.keyboard import VkKeyboard

from core.models import GoalStatus
from core.services import GoalService
from utils import helpers
from vk_bot.context import BotContext
from vk_bot.handlers.scenario import ScenarioHandler
from vk_bot.keyboards import cancel_keyboard
from vk_bot.states import GoalState
from vk_bot.user_helpers import get_or_create_user


class GoalHandler(ScenarioHandler):
    """Handler for the `/goal` command.

    Управляет состояниями:
    * menu: текущие показатели и выбор действия (установка, отключение)
    * waiting_for_goal_input: ввод количества страниц в день
    """

    priority = 10
    commands = ["/goal", "goal", "цель"]
    scenario_command = "/goal"
    initial_state = GoalState.MENU
    states = GoalState

    # ── Жизненный цикл ──────────────────────────────────────────────

    def start(self, context: BotContext) -> None:
        user = get_or_create_user(context.api, context.user_id)
        self.begin(context, GoalState.MENU, {"user_id": user.id})

    def render_menu(self, context: BotContext, state_info: dict) -> None:
        service = GoalService()
        status = service.get_goal_status(self._user_id(context, state_info))
        context.send_message(
            self._format_menu_text(status),
            keyboard=self._create_menu_keyboard(),
        )

    def render_waiting_for_goal_input(self, context: BotContext, state_info: dict) -> None:
        context.send_message(
            "Введи количество страниц в день (целое число).\n\n0 — отключить цель.",
            keyboard=cancel_keyboard(self._back_command(state_info)),
        )

    # ── Шаги ────────────────────────────────────────────────────────

    def step_menu(self, context: BotContext, state_info: dict) -> Any:
        choice = context.text.strip().lower()
        if choice == "установить":
            return GoalState.WAITING_FOR_GOAL_INPUT
        if choice == "отключить":
            self._disable(context, state_info)
            return None

        context.send_message(
            helpers.format_invalid_input("Выбери действие из клавиатуры."),
            keyboard=self._create_menu_keyboard(),
        )
        return None

    def step_waiting_for_goal_input(self, context: BotContext, state_info: dict) -> Any:
        try:
            value = int(context.text.strip())
        except ValueError:
            context.send_message(
                helpers.format_invalid_input("Введи целое число, например 20."),
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )
            return None

        if value < 0:
            context.send_message(
                helpers.format_invalid_input("Цель не может быть отрицательной."),
                keyboard=cancel_keyboard(self._back_command(state_info)),
            )
            return None

        service = GoalService()
        user_id = self._user_id(context, state_info)
        if value == 0:
            service.disable_goal(user_id)
            self.finish(context, "Цель отключена.")
            return None

        service.set_daily_goal(user_id, value)
        self.finish(context, f"Цель на день установлена: {value} стр.")
        return None

    # ── Форматирование и действия меню ──────────────────────────────

    @staticmethod
    def _format_menu_text(status: GoalStatus | None) -> str:
        if status is None:
            return (
                "Цель на день\n\n"
                "Цель на день не установлена.\n\n"
                "Нажми «Установить», чтобы задать количество страниц в день."
            )

        lines = [
            f"Цель на день: {status.goal.target} стр.",
            f"Сегодня прочитано: {status.pages_today} стр. ({status.percent}%)",
        ]
        if status.completed:
            lines.append("Цель выполнена.")
        else:
            lines.append(f"Осталось: {status.remaining} стр.")
        lines.append(helpers.format_streak(status.streak))
        lines.extend(["", "Выбери действие:"])
        return "\n".join(lines)

    def _disable(self, context: BotContext, state_info: dict) -> None:
        service = GoalService()
        if not service.disable_goal(self._user_id(context, state_info)):
            self.finish(context, "Цель не установлена.")
            return
        self.finish(context, "Цель отключена.")

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
    def _create_menu_keyboard() -> VkKeyboard:
        """Клавиатура меню целей."""
        kb = VkKeyboard()
        kb.add_button("Установить")
        kb.add_line()
        kb.add_button("Отключить")
        kb.add_button("Отмена", payload={"command": "/cancel"})
        return kb
