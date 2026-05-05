"""Скрипт для миграции данных из JSON-файлов в базу данных SQLite."""

import json
import sys
from pathlib import Path
from typing import List, Dict

from core.models import Book, User
from core.database import Database

def load_books_from_json(data_dir: str = "data") -> List[Book]:
    """Загружает книги из JSON-файла."""
    data_dir_path = Path(data_dir)
    books_file = data_dir_path / "books.json"

    if not books_file.exists():
        return []

    try:
        with open(books_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            books_data = data.get("books", [])
            return [Book.from_dict(book_data) for book_data in books_data]
    except (json.JSONDecodeError, IOError) as e:
        print(f"Ошибка при загрузке книг: {e}", file=sys.stderr)
        return []

def load_users_from_json(data_dir: str = "data") -> List[User]:
    """Загружает пользователей из JSON-файла."""
    data_dir_path = Path(data_dir)
    users_file = data_dir_path / "users.json"

    if not users_file.exists():
        return []

    try:
        with open(users_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            users_data = data.get("users", [])
            return [User.from_dict(user_data) for user_data in users_data]
    except (json.JSONDecodeError, IOError) as e:
        print(f"Ошибка при загрузке пользователей: {e}", file=sys.stderr)
        return []

def migrate_data(data_dir: str = "data") -> None:
    """Миграция данных из JSON-файлов в базу данных SQLite."""
    print("Начинаем миграцию данных из JSON в SQLite...")

    # Загружаем данные из JSON-файлов
    books = load_books_from_json(data_dir)
    users = load_users_from_json(data_dir)

    print(f"Найдено {len(users)} пользователей и {len(books)} книг для миграции.")

    # Инициализируем базу данных
    db = Database()

    # Мигрируем пользователей
    for user in users:
        db.add_or_update_user(user)

    # Мигрируем книги
    for book in books:
        db.add_or_update_book(book)

    print(f"Миграция завершена успешно!")
    print(f"База данных создана по пути: {db.db_path}")
    print(f"Перенесено {len(users)} пользователей и {len(books)} книг.")

    db.close()

if __name__ == "__main__":
    # Определяем директорию с данными
    data_dir = "data" if len(sys.argv) < 2 else sys.argv[1]

    try:
        migrate_data(data_dir)
    except Exception as e:
        print(f"Ошибка при миграции: {e}", file=sys.stderr)
        sys.exit(1)
