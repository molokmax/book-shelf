"""Репозиторий для работы с данными."""

import json
from typing import List, Optional, Dict
from pathlib import Path

from core.models import Book, User

class BookRepository:
    """Репозиторий для работы с книгами."""

    def __init__(self, data_dir: str = "data") -> None:
        """Инициализация репозитория."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.books_file = self.data_dir / "books.json"

    def get_all_books(self) -> List[Book]:
        """Получает все книги."""
        data = self._load_data(self.books_file)
        return [Book.from_dict(book_data) for book_data in data.get("books", [])]

    def get_book_by_id(self, book_id: str) -> Optional[Book]:
        """Получает книгу по ID."""
        books = self.get_all_books()
        for book in books:
            if book.id == book_id:
                return book
        return None

    def add_book(self, book: Book) -> Book:
        """Добавляет новую книгу."""
        data = self._load_data(self.books_file)
        books = data.get("books", [])

        # Проверяем, что книга с таким ID не существует
        for existing_book in books:
            if existing_book.get("id") == book.id:
                raise ValueError(f"Книга с ID {book.id} уже существует")

        books.append(book.to_dict())
        data["books"] = books
        self._save_data(self.books_file, data)
        return book

    def update_book(self, book: Book) -> Book:
        """Обновляет книгу."""
        data = self._load_data(self.books_file)
        books = data.get("books", [])

        updated_books = []
        found = False

        for existing_book in books:
            if existing_book.get("id") == book.id:
                updated_books.append(book.to_dict())
                found = True
            else:
                updated_books.append(existing_book)

        if not found:
            raise ValueError(f"Книга с ID {book.id} не найдена")

        data["books"] = updated_books
        self._save_data(self.books_file, data)
        return book

    def delete_book(self, book_id: str) -> Book:
        """Удаляет книгу по ID."""
        data = self._load_data(self.books_file)
        books = data.get("books", [])

        deleted_book = None
        updated_books = []

        for book in books:
            if book.get("id") == book_id:
                deleted_book = Book.from_dict(book)
            else:
                updated_books.append(book)

        if not deleted_book:
            raise ValueError(f"Книга с ID {book_id} не найдена")

        data["books"] = updated_books
        self._save_data(self.books_file, data)
        return deleted_book

    def get_books_by_status(self, status: str) -> List[Book]:
        """Получает книги по статусу."""
        books = self.get_all_books()
        return [book for book in books if book.status.value == status]

    def get_books_by_user_id(self, user_id: str) -> List[Book]:
        """Получает книги по ID пользователя."""
        books = self.get_all_books()
        return [book for book in books if book.user_id == user_id]

    def _ensure_file_exists(self, file_path: Path) -> None:
        """Обеспечивает существование файла."""
        if not file_path.exists():
            file_path.write_text("{}")

    def _load_data(self, file_path: Path) -> Dict:
        """Загружает данные из файла."""
        self._ensure_file_exists(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_data(self, file_path: Path, data: Dict) -> None:
        """Сохраняет данные в файл."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, data_dir: str = "data") -> None:
        """Инициализация репозитория."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.users_file = self.data_dir / "users.json"

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получает пользователя по Telegram ID."""
        data = self._load_data(self.users_file)
        users = data.get("users", [])

        for user_data in users:
            if user_data.get("telegram_id") == telegram_id:
                return User.from_dict(user_data)
        return None

    def add_user(self, user: User) -> User:
        """Добавляет нового пользователя."""
        data = self._load_data(self.users_file)
        users = data.get("users", [])

        # Проверяем, что пользователь с таким Telegram ID не существует
        for existing_user in users:
            if existing_user.get("telegram_id") == user.telegram_id:
                return User.from_dict(existing_user)

        users.append(user.to_dict())
        data["users"] = users
        self._save_data(self.users_file, data)
        return user

    def update_user(self, user: User) -> User:
        """Обновляет пользователя."""
        data = self._load_data(self.users_file)
        users = data.get("users", [])

        updated_users = []
        found = False

        for existing_user in users:
            if existing_user.get("id") == user.id:
                updated_users.append(user.to_dict())
                found = True
            else:
                updated_users.append(existing_user)

        if not found:
            raise ValueError(f"Пользователь с ID {user.id} не найден")

        data["users"] = updated_users
        self._save_data(self.users_file, data)
        return user

    def _ensure_file_exists(self, file_path: Path) -> None:
        """Обеспечивает существование файла."""
        if not file_path.exists():
            file_path.write_text("{}")

    def _load_data(self, file_path: Path) -> Dict:
        """Загружает данные из файла."""
        self._ensure_file_exists(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_data(self, file_path: Path, data: Dict) -> None:
        """Сохраняет данные в файл."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
