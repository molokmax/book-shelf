import json
from typing import Any, Dict, Optional

from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id

from core.storage import ActiveStateStorage

from . import message_chain


class BotContext:
    __slots__ = ("_vk", "_api", "_upload", "_event", "_storage")

    def __init__(self, vk, upload, event, storage: ActiveStateStorage | None = None):
        self._vk = vk
        self._api = vk.get_api()
        self._upload = upload
        self._event = event
        self._storage = storage

    @property
    def vk(self):
        return self._vk

    @property
    def api(self):
        return self._api

    @property
    def upload(self):
        return self._upload

    @property
    def event(self):
        return self._event

    @property
    def user_id(self):
        return self._event.user_id

    @property
    def peer_id(self):
        return self._event.peer_id

    @property
    def text(self):
        return self._event.text

    @property
    def payload(self):
        if hasattr(self._event, "payload") and self._event.payload:
            return json.loads(self._event.payload)
        return {}

    @property
    def command(self):
        cmd = None
        try:
            cmd = self.payload.get("command")
        except Exception:
            pass
        if not cmd:
            cmd = self._event.text.lower()
        return cmd

    def get_state(self) -> Dict[str, Any]:
        if self._storage is None:
            return {}
        return self._storage.get(self.user_id)

    def set_state(self, state: Dict[str, Any]) -> None:
        if self._storage is not None:
            self._carry_last_message_id(state)
            self._storage.save(self.user_id, state)

    def delete_state(self) -> None:
        if self._storage is not None:
            self._storage.delete(self.user_id)

    def is_active(self) -> bool:
        if self._storage is None:
            return False
        return self._storage.is_active(self.user_id)

    @property
    def command_state(self) -> Optional[str]:
        if self._storage is None:
            return None
        return self._storage.get_command(self.user_id)

    def send_message(
        self,
        message: str,
        keyboard: Optional[VkKeyboard] = None,
        attachment: Optional[str] = None,
    ) -> None:
        """Отправляет сообщение и ведёт цепочку промежуточных сообщений.

        Перед отправкой удаляет предыдущее промежуточное сообщение сценария
        (issue #44). Id нового сообщения запоминается в data стейта, только
        пока сценарий активен: финальные сообщения отправляются до
        delete_state(), и их id стирается вместе со стейтом, поэтому они
        остаются в истории навсегда.
        """
        message_chain.delete_intermediate_message(self._api, self._storage, self.user_id)

        kwargs: Dict[str, Any] = {
            "user_id": self.user_id,
            "message": message,
            "random_id": get_random_id(),
        }
        if keyboard is not None:
            kwargs["keyboard"] = keyboard.get_keyboard()
        if attachment is not None:
            kwargs["attachment"] = attachment

        response = self._api.messages.send(**kwargs)
        message_chain.remember_message_id(
            self._storage, self.user_id, message_chain.extract_message_id(response)
        )

    def _carry_last_message_id(self, state: Dict[str, Any]) -> None:
        """Сохраняет актуальный id промежуточного сообщения при перезаписи стейта.

        Хендлеры мутируют локальную копию state_info, прочитанную до отправки,
        и могут записать устаревший last_message_id. Берём значение из
        хранилища: его обновляет send_message сразу после отправки.
        """
        message_id = message_chain.current_message_id(self._storage, self.user_id)
        if message_id is None:
            return
        data = state.get("data")
        if isinstance(data, dict):
            data[message_chain.LAST_MESSAGE_KEY] = message_id
        else:
            state["data"] = {message_chain.LAST_MESSAGE_KEY: message_id}
