"""Тесты хранения тегов: справочник, привязки, каскады, сортировка, сервисы."""

import pytest

import core.db as core_db
from core.database import Database
from core.models import Book, User
from core.repository import TagRepository
from core.services import BookService, TagService, UserService


@pytest.fixture
def db(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "tags.db"))
    monkeypatch.setattr(core_db, "_db_instance", database)
    yield database
    database.close()


def add_user(db: Database, user_id: str):
    return db.add_or_update_user(User(id=user_id, external_id=hash(user_id) % 10**9))


def make_book(user_id: str, tags: list[str]) -> Book:
    return Book(title="Book", author="Author", tags=tags, pages=100, user_id=user_id)


def test_book_tags_roundtrip(db: Database):
    add_user(db, "user-1")
    book = db.add_or_update_book(make_book("user-1", ["Фантастика", "Классика"]))

    loaded = db.get_book_by_id(book.id)
    # Алфавит без учёта регистра
    assert loaded.tags == ["Классика", "Фантастика"]


def test_tags_are_per_user(db: Database):
    add_user(db, "user-1")
    add_user(db, "user-2")
    db.add_or_update_book(make_book("user-1", ["Классика"]))
    db.add_or_update_book(make_book("user-2", ["Классика"]))

    len(TagRepository(db).get_user_tags("user-1"))
    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM tags WHERE name = 'Классика'")
        # У каждого пользователя своя запись тега
        assert cursor.fetchone()[0] == 2


def test_casefold_dedupe_keeps_first_form(db: Database):
    add_user(db, "user-1")
    db.add_or_update_book(make_book("user-1", ["Tech", "tech", "  tech  "]))

    repo = TagRepository(db)
    assert repo.get_user_tags("user-1") == ["Tech"]

    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM tags WHERE user_id = 'user-1'")
        assert cursor.fetchone()[0] == 1


def test_dictionary_keeps_tags_after_detach(db: Database):
    add_user(db, "user-1")
    book = db.add_or_update_book(make_book("user-1", ["Классика"]))

    # Снимаем тег с книги: привязки пустые, тег остаётся в справочнике
    book.tags = []
    db.add_or_update_book(book)

    repo = TagRepository(db)
    assert repo.get_user_tags("user-1") == ["Классика"]
    assert repo.get_used_tags("user-1") == []


def test_delete_book_cascades_bindings(db: Database):
    add_user(db, "user-1")
    book = db.add_or_update_book(make_book("user-1", ["Классика"]))
    db.delete_book(book.id)

    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM book_tags")
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT COUNT(*) FROM tags WHERE user_id = 'user-1'")
        assert cursor.fetchone()[0] == 1


def test_tag_service_reads_dictionary_and_used(db: Database):
    add_user(db, "user-1")
    book = db.add_or_update_book(make_book("user-1", ["Классика"]))
    db.add_or_update_book(make_book("user-1", []))

    service = TagService()
    assert service.get_user_tags("user-1") == ["Классика"]
    assert service.get_used_tags("user-1") == ["Классика"]

    # Отвязываем тег: он уходит из используемых, но остаётся в справочнике
    book.tags = []
    db.add_or_update_book(book)
    assert service.get_user_tags("user-1") == ["Классика"]
    assert service.get_used_tags("user-1") == []


def test_book_service_get_all_tags_uses_bindings(db: Database):
    user_service = UserService()
    user = user_service.get_or_create_user(1, lambda uid: User(id=str(uid), external_id=uid))
    book_service = BookService()
    book_service.create_book(title="T", author="A", tags=["Классика"], pages=10, user_id=user.id)
    unused = book_service.create_book(title="U", author="A", tags=[], pages=10, user_id=user.id)

    assert book_service.get_all_tags(user.id) == ["Классика"]

    book_service.update_book_tags(unused.id, ["Tech", "классика"])
    # «классика» резолвится casefold в существующий «Классика»
    assert book_service.get_all_tags(user.id) == ["Tech", "Классика"]


def test_create_book_with_tags_and_relist(db: Database):
    user_service = UserService()
    user = user_service.get_or_create_user(2, lambda uid: User(id=str(uid), external_id=uid))
    book_service = BookService()
    book = book_service.create_book(
        title="T", author="A", tags=["b", "a"], pages=10, user_id=user.id
    )
    reloaded = book_service.get_book_by_id(book.id)
    assert reloaded.tags == ["a", "b"]
