"""Repository for persisting per‑user state in SQLite.

The table ``user_state`` will be added later (see task 3.1). Until the migration is applied the
repository gracefully falls back to an empty dict.
"""

import json
from typing import Any, Dict, Optional

from core.database import Database


class UserStateRepository:
    """Хранилище состояния пользователя.

    Таблица ``user_state`` имеет колонки:
        user_id TEXT PRIMARY KEY,
        json TEXT
    """

    def __init__(self) -> None:
        self.db = Database()

    def get_state(self, user_id: str) -> Dict[str, Any]:
        """Возвращает состояние пользователя как словарь.

        Если запись отсутствует – возвращает пустой словарь.
        """
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT json FROM user_state WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return {}
            return {}

    def save_state(self, user_id: str, state: Dict[str, Any]) -> None:
        """Сохраняет состояние пользователя.

        ``state`` сериализуется в JSON и сохраняется в таблице ``user_state``.
        """
        json_state = json.dumps(state)
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "INSERT OR REPLACE INTO user_state (user_id, json) VALUES (?, ?)",
                (user_id, json_state),
            )
