import sqlite3


def add_link_column(conn: sqlite3.Connection):
    # Добавляем колонку link, если её ещё нет
    try:
        conn.execute("ALTER TABLE books ADD COLUMN link TEXT")
    except sqlite3.OperationalError:
        pass  # колонка уже существует
