"""История шагов сценария для кнопки «Назад» (issue #59).

История — стек снимков ``{state, data}`` в ``state_info["history"]``.
Снимок фиксируется только при смене шага: повторный рендер текущего шага
(неверный ввод, toggle тегов, пагинация) историю не раздувает. При возврате
назад снимок восстанавливается целиком, поэтому значения, введённые на
«будущих» шагах, отбрасываются и заполняются заново.
"""

from copy import deepcopy
from typing import Any, Dict, Optional

from vk_bot.message_chain import LAST_MESSAGE_KEY

HISTORY_KEY = "history"


def record_transition(state_info: Dict[str, Any], next_state: Any) -> None:
    """Фиксирует переход на новый шаг и сохраняет снимок прежнего в историю.

    Вызывается и ``ScenarioHandler.goto()``, и переиспользуемыми flow,
    которые меняют шаг напрямую. Если прежнего шага нет (корневой экран)
    или шаг не меняется, снимок не создаётся.
    """
    current = state_info.get("state")
    next_value = str(next_state)
    if current and current != next_value:
        data = {
            key: deepcopy(value)
            for key, value in state_info.get("data", {}).items()
            if key != LAST_MESSAGE_KEY
        }
        state_info.setdefault(HISTORY_KEY, []).append({"state": current, "data": data})
    state_info["state"] = next_value


def pop_previous(state_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Возвращает к предыдущему шагу: восстанавливает снимок из истории.

    Возвращает снятый снимок или ``None``, если история пуста (первый шаг).
    """
    history = state_info.get(HISTORY_KEY) or []
    if not history:
        return None
    snapshot = history.pop()
    state_info["state"] = snapshot["state"]
    state_info["data"] = snapshot["data"]
    return snapshot


def available_back_command(state_info: Dict[str, Any], command: str) -> Optional[str]:
    """Команда владельца для кнопки «Назад» или ``None`` на первом шаге."""
    return command if state_info.get(HISTORY_KEY) else None
