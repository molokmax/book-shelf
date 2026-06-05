import json


class BotContext:
    __slots__ = ("_vk", "_api", "_upload", "_event")

    def __init__(self, vk, upload, event):
        self._vk = vk
        self._api = vk.get_api()
        self._upload = upload
        self._event = event

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
