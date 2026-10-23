"""Тесты миграции read_stats.user_id."""

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
