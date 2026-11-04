"""Тесты миграций read_stats.user_id и переноса тегов в tags/book_tags."""

import sqlite3

from core.database import Database


def create_pre_migration_db(path):
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE books (id TEXT PRIMARY KEY, user_id TEXT NOT NULL)")
    conn.execute(
        "CREATE TABLE read_stats ("
        "id TEXT PRIMARY KEY, book_id TEXT NOT NULL, "
        "pages_read INTEGER NOT NULL, read_date TEXT NOT NULL)"
    )
    conn.execute("INSERT INTO books (id, user_id) VALUES ('book-1', 'user-1')")
    conn.execute(
        "INSERT INTO read_stats (id, book_id, pages_read, read_date) "
        "VALUES ('stat-1', 'book-1', 10, '2026-01-01T10:00:00')"
    )
    conn.execute(
        "INSERT INTO read_stats (id, book_id, pages_read, read_date) "
        "VALUES ('stat-2', 'deleted-book', 5, '2026-01-01T11:00:00')"
    )
    conn.commit()
    conn.close()


def fetch_stats(db: Database):
    with db.get_cursor() as cur:
        cur.execute("SELECT id, user_id FROM read_stats ORDER BY id")
        return cur.fetchall()


def test_migration_backfills_user_id(tmp_path):
    db_path = tmp_path / "old.db"
    create_pre_migration_db(db_path)

    db = Database(str(db_path))

    assert fetch_stats(db) == [("stat-1", "user-1"), ("stat-2", None)]
    db.close()


def test_migration_is_idempotent(tmp_path):
    db_path = tmp_path / "old.db"
    create_pre_migration_db(db_path)

    first = Database(str(db_path))
    before = fetch_stats(first)
    first.close()

    second = Database(str(db_path))
    after = fetch_stats(second)
    second.close()

    assert before == after == [("stat-1", "user-1"), ("stat-2", None)]


def test_new_database_has_goals_and_user_id(tmp_path):
    db = Database(str(tmp_path / "new.db"))

    with db.get_cursor() as cur:
        cur.execute("PRAGMA table_info(read_stats)")
        read_stats_columns = {row[1] for row in cur.fetchall()}
        cur.execute("PRAGMA table_info(goals)")
        goals_columns = {row[1] for row in cur.fetchall()}

    db.close()

    assert "user_id" in read_stats_columns
    assert {"id", "user_id", "kind", "target", "created_at", "updated_at"} <= goals_columns


# ── Перенос тегов в tags/book_tags ────────────────────────────────────────────


OLD_BOOKS_SCHEMA = """
CREATE TABLE books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    tags TEXT,
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
"""


def insert_legacy_book(conn, book_id, user_id, raw_tags):
    """Добавляет книгу в таблицу books ещё с колонкой tags."""
    conn.execute(
        "INSERT INTO books (id, title, author, tags, pages, current_page, status, "
        "created_at, updated_at, user_id) "
        "VALUES (?, 'T', 'A', ?, 100, 0, 'want_to_read', "
        "'2026-01-01T00:00:00', '2026-01-01T00:00:00', ?)",
        (book_id, raw_tags, user_id),
    )


def open_pre_tags_db(tmp_path, name="tags-old.db"):
    """База со старой схемой books (с колонкой tags), без таблиц тегов."""
    path = tmp_path / name
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE users (id TEXT PRIMARY KEY, external_id INTEGER UNIQUE NOT NULL)")
    conn.execute(OLD_BOOKS_SCHEMA)
    return path, conn


def insert_legacy_user(conn, user_id, external_id):
    conn.execute("INSERT INTO users (id, external_id) VALUES (?, ?)", (user_id, external_id))


def fetch_tags_state(db: Database):
    """Срез тегов: справочник, привязки и книги."""
    with db.get_cursor() as cur:
        cur.execute("SELECT user_id, name FROM tags ORDER BY user_id, name")
        dictionary = cur.fetchall()
        cur.execute("SELECT book_id, tag_id FROM book_tags ORDER BY book_id, tag_id")
        bindings = cur.fetchall()
    with db.get_cursor() as cur:
        cur.execute("PRAGMA table_info(books)")
        book_columns = {row[1] for row in cur.fetchall()}
    return {"dictionary": dictionary, "bindings": bindings, "book_columns": book_columns}


def test_books_tags_migrated(tmp_path):
    path, conn = open_pre_tags_db(tmp_path)
    insert_legacy_user(conn, "user-1", 1)
    insert_legacy_user(conn, "user-2", 2)
    insert_legacy_book(conn, "book-1", "user-1", "['Tech', 'Фантастика']")
    insert_legacy_book(conn, "book-2", "user-2", "['Классика']")
    conn.commit()
    conn.close()

    db = Database(str(path))
    state = fetch_tags_state(db)

    assert "tags" not in state["book_columns"]
    names_by_user: dict[str, set] = {}
    for user_id, name in state["dictionary"]:
        names_by_user.setdefault(user_id, set()).add(name)
    assert names_by_user["user-1"] == {"Tech", "Фантастика"}
    assert names_by_user["user-2"] == {"Классика"}
    assert state["bindings"], "привязки book_tags должны появиться"
    db.close()


def test_migration_is_idempotent_for_tags(tmp_path):
    path, conn = open_pre_tags_db(tmp_path)
    insert_legacy_user(conn, "user-1", 1)
    insert_legacy_book(conn, "book-1", "user-1", "['Tech', 'Фантастика']")
    conn.commit()
    conn.close()

    first = Database(str(path))
    before = fetch_tags_state(first)
    first.close()

    second = Database(str(path))
    after = fetch_tags_state(second)
    second.close()

    assert before == after
    assert "tags" not in after["book_columns"]


def test_migration_dedupes_casefold(tmp_path):
    path, conn = open_pre_tags_db(tmp_path)
    insert_legacy_user(conn, "user-1", 1)
    insert_legacy_book(conn, "book-1", "user-1", "['Tech']")
    insert_legacy_book(conn, "book-2", "user-1", "['tech']")
    conn.commit()
    conn.close()

    db = Database(str(path))
    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tags WHERE user_id = 'user-1'")
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT name FROM tags WHERE user_id = 'user-1'")
        # Каноническая форма: первое встреченное имя
        assert cur.fetchone()[0] == "Tech"
        # Номер тега один, привязаны обе книги
        cur.execute("SELECT COUNT(*) FROM tags WHERE user_id = 'user-1' AND name = 'Tech'")
        assert cur.fetchone()[0] == 1
        cur.execute(
            "SELECT COUNT(DISTINCT bt.book_id) FROM book_tags bt "
            "JOIN tags t ON t.id = bt.tag_id WHERE t.name = 'Tech'"
        )
        assert cur.fetchone()[0] == 2
    db.close()


def test_migration_skips_damaged_values(tmp_path):
    path, conn = open_pre_tags_db(tmp_path)
    insert_legacy_user(conn, "user-1", 1)
    insert_legacy_book(conn, "book-1", "user-1", "не-parse значение [")
    conn.commit()
    conn.close()

    db = Database(str(path))
    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tags")
        assert cur.fetchone()[0] == 0
        cur.execute("SELECT COUNT(*) FROM book_tags")
        assert cur.fetchone()[0] == 0
        # Книга сохраняется, колонка всё равно удаляется
        cur.execute("SELECT COUNT(*) FROM books")
        assert cur.fetchone()[0] == 1
        cur.execute("PRAGMA table_info(books)")
        assert "tags" not in {row[1] for row in cur.fetchall()}
    db.close()


def test_new_database_schema_has_tag_tables(tmp_path):
    db = Database(str(tmp_path / "new.db"))

    with db.get_cursor() as cur:
        cur.execute("PRAGMA table_info(books)")
        book_columns = {row[1] for row in cur.fetchall()}
        cur.execute("PRAGMA table_info(tags)")
        tags_columns = {row[1] for row in cur.fetchall()}
        cur.execute("PRAGMA table_info(book_tags)")
        book_tags_columns = {row[1] for row in cur.fetchall()}

    db.close()

    assert "tags" not in book_columns
    assert {"id", "user_id", "name", "created_at"} <= tags_columns
    assert {"book_id", "tag_id"} <= book_tags_columns
