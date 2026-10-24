"""Механизм очистки промежуточных сообщений бота из истории чата (issue #44).

Промежуточное сообщение - сообщение, которое переспрашивает пользователя и
ждёт продолжения сценария. Каждое новое сообщение бота в активном сценарии
удаляет предыдущее промежуточное, поэтому в истории остаётся только финал.
Id последнего промежуточного сообщения хранится в data стейта пользователя
под ключом ``last_message_id``.
"""

from typing import Any, Optional

from utils import logger

log = logger.setup_logger(__name__)

LAST_MESSAGE_KEY = "last_message_id"


def delete_intermediate_message(api: Any, storage: Any, user_id: Any) -> None:
    """Удаляет из чата последнее промежуточное сообщение сценария.

    Ошибки VK API молча глотаются: сообщение могло устареть (для
    delete_for_all срок - 24 часа) или уже быть удалённым.
    """
    if storage is None:
        return
    state = storage.get(user_id)
    if not state:
        return
    message_id = state.get("data", {}).get(LAST_MESSAGE_KEY)
    if not message_id:
        return
    try:
        api.messages.delete(message_ids=[message_id], delete_for_all=1)
    except Exception as e:
        log.debug("Не удалось удалить промежуточное сообщение %s: %s", message_id, e)


def remember_message_id(storage: Any, user_id: Any, message_id: Optional[int]) -> None:
    """Запоминает id отправленного сообщения, если сценарий ещё активен."""
    if storage is None or message_id is None:
        return
    state = storage.get(user_id)
    if not state:
        return
    state.setdefault("data", {})[LAST_MESSAGE_KEY] = message_id
    storage.save(user_id, state)


def current_message_id(storage: Any, user_id: Any) -> Optional[int]:
    """Возвращает id последнего промежуточного сообщения активного сценария."""
    if storage is None:
        return None
    state = storage.get(user_id)
    if not state:
        return None
    return state.get("data", {}).get(LAST_MESSAGE_KEY)


def extract_message_id(response: Any) -> Optional[int]:
    """Достаёт message_id из ответа messages.send (устойчиво к заглушкам)."""
    if isinstance(response, dict):
        message_id = response.get("message_id")
        return message_id if isinstance(message_id, int) else None
    if isinstance(response, int):
        return response
    return None
