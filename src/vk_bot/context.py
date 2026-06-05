import json
from typing import Any, Dict, Optional

from core.storage import ActiveStateStorage


class BotContext:
    __slots__ = ("_vk", "_api", "_upload", "_event", "_storage")

    def __init__(
        self, vk, upload, event, storage: ActiveStateStorage | None = None
    ):
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
