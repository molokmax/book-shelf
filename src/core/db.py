"""Модуль для управления единственным экземпляром базы данных."""

from core.database import Database

# Глобальный экземпляр базы данных
_db_instance = None

def get_db(db_path: str = "data/database.db") -> Database:
    """Возвращает глобальный экземпляр базы данных."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance

def close_db() -> None:
    """Закрывает подключение к базе данных."""
    global _db_instance
    if _db_instance is not None:
        _db_instance.close()
        _db_instance = None
