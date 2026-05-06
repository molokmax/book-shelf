"""Модели данных для Book Shelf."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime

class ReadingStatus(str, Enum):
    """Статусы чтения книги."""
    WANT_TO_READ = "want_to_read"
    READING = "reading"
    READ = "read"
    POSTPONED = "postponed"

@dataclass
class Book:
    """Модель книги."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)
    pages: int = 0
    current_page: int = 0
    status: ReadingStatus = ReadingStatus.WANT_TO_READ
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    cover_image: Optional[str] = None
    notes: Optional[str] = None
    reading_start_date: Optional[datetime] = None
    reading_end_date: Optional[datetime] = None
    user_id: str = ""

    def update_progress(self, new_page: int) -> None:
        """Обновляет прогресс чтения по текущей странице."""
        self.current_page = max(0, min(self.pages, new_page))
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Конвертирует книгу в словарь для сохранения."""
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "tags": self.tags,
            "pages": self.pages,
            "current_page": self.current_page,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "cover_image": self.cover_image,
            "notes": self.notes,
            "reading_start_date": self.reading_start_date.isoformat() if self.reading_start_date else None,
            "reading_end_date": self.reading_end_date.isoformat() if self.reading_end_date else None,
            "user_id": self.user_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        """Создаёт книгу из словаря."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            author=data.get("author", ""),
            tags=data.get("tags", []),
            pages=data.get("pages", 0),
            current_page=data.get("current_page", data.get("progress", 0)),  # Поддержка миграции
            status=ReadingStatus(data.get("status", ReadingStatus.WANT_TO_READ.value)),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            cover_image=data.get("cover_image"),
            notes=data.get("notes"),
            reading_start_date=datetime.fromisoformat(data.get("reading_start_date")) if data.get("reading_start_date") else None,
            reading_end_date=datetime.fromisoformat(data.get("reading_end_date")) if data.get("reading_end_date") else None,
            user_id=data.get("user_id", "")
        )

@dataclass
class User:
    """Модель пользователя."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    external_id: int = 0
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Конвертирует пользователя в словарь для сохранения."""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Создаёт пользователя из словаря."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            external_id=data.get("external_id", 0),
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            last_active=datetime.fromisoformat(data.get("last_active", datetime.now().isoformat()))
        )
