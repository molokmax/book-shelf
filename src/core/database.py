"""Модуль для работы с базой данных SQLite."""

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from core.migrations import add_link_column
from core.models import Book, User


class Database:
    """Класс для работы с базой данных SQLite."""

    _book_column_list = [
        "id",
        "title",
        "author",
        "tags",
        "pages",
        "current_page",
        "status",
        "created_at",
        "updated_at",
        "cover_image",
        "notes",
        "link",
        "reading_start_date",
        "reading_end_date",
        "user_id",
    ]

    def __init__(self, db_path: str = "data/database.db") -> None:
        """Инициализация базы данных."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)

        # Создаём подключение к базе данных
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute(
            "PRAGMA foreign_keys = ON"
        )  # Включаем поддержку внешних ключей
        self.conn.execute(
            "PRAGMA journal_mode = WAL"
        )  # Используем WAL для лучшей производительности
        self.conn.execute("PRAGMA busy_timeout = 5000")  # Таймаут при блокировке

        # Создаём таблицы при инициализации
        self._create_tables()

        # Миграции
        add_link_column(self.conn)

    def _create_tables(self) -> None:
        """Создаёт таблицы в базе данных."""
        cursor = self.conn.cursor()

        # Таблица пользователей
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            external_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TEXT NOT NULL,
            last_active TEXT NOT NULL
        )
        """)

        # Таблица книг
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            tags TEXT,  -- Хранится как JSON-строка
            pages INTEGER NOT NULL,
            current_page INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            cover_image TEXT,
            notes TEXT,
            link TEXT,
            reading_start_date TEXT,
            reading_end_date TEXT,
            user_id TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        # Таблица статистики чтения
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS read_stats (
            id TEXT PRIMARY KEY,
            book_id TEXT NOT NULL,
            pages_read INTEGER NOT NULL,
            read_date TEXT NOT NULL,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
        """)

        self.conn.commit()

    @contextmanager
    def get_cursor(self) -> sqlite3.Cursor:
        """Контекстный менеджер для получения курсора с автоматическим коммитом."""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()

    def close(self) -> None:
        """Закрывает подключение к базе данных."""
        self.conn.close()

    def __enter__(self) -> "Database":
        """Контекстный менеджер для работы с базой данных."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Закрывает подключение при выходе из контекста."""
        self.close()

    def add_reading_stat(
        self, book_id: str, pages_read: int, read_date: str | None = None
    ) -> str:
        """Вставляет запись о статистике чтения в таблицу `read_stats`."""
        if read_date is None:
            read_date = datetime.now().isoformat()
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO read_stats (id, book_id, pages_read, read_date) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), book_id, pages_read, read_date),
            )
            return cursor.lastrowid

    def add_or_update_user(self, user: "User") -> "User":
        """Добавляет или обновляет пользователя в базе данных."""

        with self.get_cursor() as cursor:
            cursor.execute(
                """
            INSERT OR REPLACE INTO users
            (id, external_id, username, first_name, last_name, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user.id,
                    user.external_id,
                    user.username,
                    user.first_name,
                    user.last_name,
                    user.created_at.isoformat(),
                    user.last_active.isoformat(),
                ),
            )

            cursor.execute("SELECT * FROM users WHERE id = ?", (user.id,))
            row = cursor.fetchone()

            if row:
                return User.from_dict(
                    {
                        "id": row[0],
                        "external_id": row[1],
                        "username": row[2],
                        "first_name": row[3],
                        "last_name": row[4],
                        "created_at": row[5],
                        "last_active": row[6],
                    }
                )
            return user

    def get_user_by_id(self, user_id: str) -> Optional["User"]:
        """Получает пользователя по ID."""

        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if row:
                return User.from_dict(
                    {
                        "id": row[0],
                        "external_id": row[1],
                        "username": row[2],
                        "first_name": row[3],
                        "last_name": row[4],
                        "created_at": row[5],
                        "last_active": row[6],
                    }
                )
            return None

    def get_user_by_external_id(self, external_id: int) -> Optional["User"]:
        """Получает пользователя по Telegram ID."""

        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE external_id = ?", (external_id,))
            row = cursor.fetchone()

            if row:
                return User.from_dict(
                    {
                        "id": row[0],
                        "external_id": row[1],
                        "username": row[2],
                        "first_name": row[3],
                        "last_name": row[4],
                        "created_at": row[5],
                        "last_active": row[6],
                    }
                )
            return None

    def add_or_update_book(self, book: "Book") -> "Book":
        """Добавляет или обновляет книгу в базе данных."""

        with self.get_cursor() as cursor:
            cursor.execute(
                """
            INSERT OR REPLACE INTO books
            (id, title, author, tags, pages, current_page, status, created_at, updated_at,
              cover_image, notes, link, reading_start_date, reading_end_date, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    book.id,
                    book.title,
                    book.author,
                    str(book.tags) if book.tags else "[]",
                    book.pages,
                    book.current_page,
                    book.status.value,
                    book.created_at.isoformat(),
                    book.updated_at.isoformat(),
                    book.cover_image,
                    book.notes,
                    book.link,
                    (
                        book.reading_start_date.isoformat()
                        if book.reading_start_date
                        else None
                    ),
                    (
                        book.reading_end_date.isoformat()
                        if book.reading_end_date
                        else None
                    ),
                    book.user_id,
                ),
            )

            sql = f"SELECT {", ".join(self._book_column_list)} FROM books WHERE id = ?"
            cursor.execute(sql, (book.id,))
            row = cursor.fetchone()

            if row:
                return Book.from_dict(
                    {
                        "id": row[0],
                        "title": row[1],
                        "author": row[2],
                        "tags": eval(row[3]) if row[3] else [],
                        "pages": row[4],
                        "current_page": row[5],
                        "status": row[6],
                        "created_at": row[7],
                        "updated_at": row[8],
                        "cover_image": row[9],
                        "notes": row[10],
                        "link": row[11],
                        "reading_start_date": row[12],
                        "reading_end_date": row[13],
                        "user_id": row[14],
                    }
                )
            return book

    def get_book_by_id(self, book_id: str) -> Optional["Book"]:
        """Получает книгу по ID."""

        with self.get_cursor() as cursor:
            sql = f"SELECT {", ".join(self._book_column_list)} FROM books WHERE id = ?"
            cursor.execute(sql, (book_id,))
            row = cursor.fetchone()

            if row:
                return Book.from_dict(
                    {
                        "id": row[0],
                        "title": row[1],
                        "author": row[2],
                        "tags": eval(row[3]) if row[3] else [],
                        "pages": row[4],
                        "current_page": row[5],
                        "status": row[6],
                        "created_at": row[7],
                        "updated_at": row[8],
                        "cover_image": row[9],
                        "notes": row[10],
                        "link": row[11],
                        "reading_start_date": row[12],
                        "reading_end_date": row[13],
                        "user_id": row[14],
                    }
                )
            return None

    def get_all_books(self) -> List["Book"]:
        """Получает все книги."""

        with self.get_cursor() as cursor:
            sql = f"SELECT {", ".join(self._book_column_list)} FROM books ORDER BY updated_at DESC"
            cursor.execute(sql)
            rows = cursor.fetchall()

            return [
                Book.from_dict(
                    {
                        "id": row[0],
                        "title": row[1],
                        "author": row[2],
                        "tags": eval(row[3]) if row[3] else [],
                        "pages": row[4],
                        "current_page": row[5],
                        "status": row[6],
                        "created_at": row[7],
                        "updated_at": row[8],
                        "cover_image": row[9],
                        "notes": row[10],
                        "link": row[11],
                        "reading_start_date": row[12],
                        "reading_end_date": row[13],
                        "user_id": row[14],
                    }
                )
                for row in rows
            ]

    def get_books_by_user_id(self, user_id: str) -> List["Book"]:
        """Получает книги по ID пользователя."""

        with self.get_cursor() as cursor:
            sql = f"SELECT {", ".join(self._book_column_list)} FROM books WHERE user_id = ? ORDER BY updated_at DESC"
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()

            return [
                Book.from_dict(
                    {
                        "id": row[0],
                        "title": row[1],
                        "author": row[2],
                        "tags": eval(row[3]) if row[3] else [],
                        "pages": row[4],
                        "current_page": row[5],
                        "status": row[6],
                        "created_at": row[7],
                        "updated_at": row[8],
                        "cover_image": row[9],
                        "notes": row[10],
                        "link": row[11],
                        "reading_start_date": row[12],
                        "reading_end_date": row[13],
                        "user_id": row[14],
                    }
                )
                for row in rows
            ]

    def get_books_by_status(self, status: str) -> List["Book"]:
        """Получает книги по статусу."""

        with self.get_cursor() as cursor:
            sql = f"SELECT {", ".join(self._book_column_list)} FROM books WHERE status = ? ORDER BY updated_at DESC"
            cursor.execute(sql, (status,))
            rows = cursor.fetchall()

            return [
                Book.from_dict(
                    {
                        "id": row[0],
                        "title": row[1],
                        "author": row[2],
                        "tags": eval(row[3]) if row[3] else [],
                        "pages": row[4],
                        "current_page": row[5],
                        "status": row[6],
                        "created_at": row[7],
                        "updated_at": row[8],
                        "cover_image": row[9],
                        "notes": row[10],
                        "link": row[11],
                        "reading_start_date": row[12],
                        "reading_end_date": row[13],
                        "user_id": row[14],
                    }
                )
                for row in rows
            ]

    def delete_book(self, book_id: str) -> Optional["Book"]:
        """Удаляет книгу по ID."""

        # Получаем книгу перед удалением
        book = self.get_book_by_id(book_id)
        if not book:
            return None

        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))

        return book

    def get_all_users(self) -> List["User"]:
        """Получает всех пользователей."""

        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users ORDER BY last_active DESC")
            rows = cursor.fetchall()

            return [
                User.from_dict(
                    {
                        "id": row[0],
                        "external_id": row[1],
                        "username": row[2],
                        "first_name": row[3],
                        "last_name": row[4],
                        "created_at": row[5],
                        "last_active": row[6],
                    }
                )
                for row in rows
            ]
