"""Базовый класс многошагового сценария.

Сценарий объявляет перечисление шагов (``states``) и начальный шаг
(``initial_state``), а методы шагов называются ``step_<state>``:
они получают ``context`` и ``state_info`` и возвращают имя следующего
шага или ``None``, если пользователь остаётся в текущем шаге.

Промпт шага — необязательный метод ``render_<state>``, который вызывается
после сохранения состояния. Полнота покрытия проверяется на импорте.
"""

from enum import StrEnum
from typing import Any, ClassVar, Dict, Optional, Type

from core.storage import ActiveStateStorage
from vk_bot.context import BotContext
from vk_bot.keyboards import main_keyboard
from vk_bot.navigation import available_back_command, pop_previous, record_transition

from .base import AbstractCommandHandler


class ScenarioHandler(AbstractCommandHandler):
    """Каркас многошаговой команды."""

    initial_state: ClassVar[StrEnum]
    states: ClassVar[Type[StrEnum]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        states = cls.__dict__.get("states")
        if states is None:
            return
        missing = [
            state.value
            for state in states
            if not callable(getattr(cls, f"step_{state.value}", None))
        ]
        if missing:
            methods = ", ".join(f"step_{value}" for value in missing)
            raise TypeError(f"{cls.__name__}: не объявлены шаги {methods}")

    # ── Основной цикл ───────────────────────────────────────────────

    def _handle(self, context: BotContext) -> Any:
        if self._is_back(context):
            self._handle_back(context)
            return True

        state_info = context.get_state()

        if not context.is_active():
            self.start(context)
            return True

        if state_info.get("command") != self.scenario_command:
            # Стейт есть, но владелец неизвестен: продолжать нечего
            self.reset_unknown_state(context)
            return True

        if self._is_restart(context):
            self.start(context)
            return True

        state = state_info.get("state")
        if state not in {member.value for member in self.states}:
            self.reset_unknown_state(context)
            return True

        next_state = getattr(self, f"step_{state}")(context, state_info)
        if next_state is not None:
            self.goto(context, next_state, state_info)
        return True

    def _back_command(self, state_info: Dict[str, Any]) -> Optional[str]:
        """Команда для кнопки «Назад» или ``None`` на первом шаге."""
        return available_back_command(state_info, self.scenario_command)

    def _is_back(self, context: BotContext) -> bool:
        """Кнопка «Назад» текущего сценария (issue #59)."""
        payload = context.payload
        return payload.get("command") == self.scenario_command and payload.get("action") == "back"

    def _handle_back(self, context: BotContext) -> None:
        """Возврат к предыдущему шагу: снимок состояния + повторный промпт.

        Бизнес-обработчик шага не вызывается: никаких записей в БД и внешних
        запросов, только восстановление состояния и перерисовка.
        """
        state_info = context.get_state()
        if not context.is_active() or state_info.get("command") != self.scenario_command:
            # Устаревшая кнопка: сценарий уже завершён, перезапускать не нужно
            context.send_message("Сценарий уже завершён.", keyboard=main_keyboard())
            return

        if pop_previous(state_info) is None:
            # Первый шаг: кнопка скрыта, нажатие устаревшей кнопки игнорируем
            return

        context.set_state(state_info)
        render = getattr(self, f"render_{state_info['state']}", None)
        if render is not None:
            render(context, state_info)

    def _is_restart(self, context: BotContext) -> bool:
        """Повторный ввод своей команды перезапускает сценарий."""
        if not self.can_handle(context.command):
            return False
        payload = context.payload
        if payload.get("command"):
            # Payload-кнопка команды, а не действие шага (toggle/done/page)
            return "action" not in payload
        return (context.text or "").strip().startswith("/")

    # ── Жизненный цикл ──────────────────────────────────────────────

    def start(self, context: BotContext) -> None:
        """Вход в сценарий: начальный шаг с пустыми данными."""
        self.begin(context, self.initial_state)

    def begin(
        self,
        context: BotContext,
        state: StrEnum,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Начинает сценарий с нового состояния."""
        state_info = ActiveStateStorage.new_state(self.scenario_command, str(state), data or {})
        self.goto(context, state, state_info)

    def goto(self, context: BotContext, state: StrEnum, state_info: Dict[str, Any]) -> None:
        """Сохраняет шаг (с записью в историю «Назад») и отправляет его промпт."""
        record_transition(state_info, state)
        state_info["command"] = self.scenario_command
        state_info.setdefault("data", {})
        context.set_state(state_info)

        render = getattr(self, f"render_{state}", None)
        if render is not None:
            render(context, state_info)

    def finish(self, context: BotContext, message: str, keyboard: Any = None) -> None:
        """Завершает сценарий: финальное сообщение до удаления состояния."""
        context.send_message(message, keyboard=keyboard or main_keyboard())
        context.delete_state()

    def reset_unknown_state(self, context: BotContext) -> None:
        """Сбрасывает сценарий с неизвестным шагом."""
        self.finish(
            context,
            f"⚠️ Не удалось продолжить сценарий. Начни заново: {self.scenario_command}",
        )
