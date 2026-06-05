"""ActiveStateStorage — обёртка над UserStateRepository для стейта."""

from typing import Any, Dict, Optional

from core.repository import UserStateRepository


class ActiveStateStorage:
    """Управление пользовательским стейтом через SQLite-персистентность.

    Предоставляет удобные методы для работы со структурой стейта:
    {"command": str, "state": str, "data": dict}
    """

    def __init__(self, repository: UserStateRepository | None = None) -> None:
        self._repository = repository or UserStateRepository()

    def get(self, user_id: str) -> Dict[str, Any]:
        return self._repository.get_state(user_id)

    def save(self, user_id: str, state: Dict[str, Any]) -> None:
        self._repository.save_state(user_id, state)

    def delete(self, user_id: str) -> None:
        self._repository.delete_state(user_id)

    def is_active(self, user_id: str) -> bool:
        state = self.get(user_id)
        return bool(state)

    def get_command(self, user_id: str) -> Optional[str]:
        state = self.get(user_id)
        return state.get("command") if state else None

    def get_current_state(self, user_id: str) -> Optional[str]:
        state = self.get(user_id)
        return state.get("state") if state else None

    @staticmethod
    def new_state(command: str, state: str, data: dict) -> Dict[str, Any]:
        return {"command": command, "state": state, "data": data}
