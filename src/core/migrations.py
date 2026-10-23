import sqlite3


def add_link_column(conn: sqlite3.Connection):
    # Добавляем колонку link, если её ещё нет
    try:
        conn.execute("ALTER TABLE books ADD COLUMN link TEXT")
    except sqlite3.OperationalError:
        pass  # колонка уже существует


def add_read_stats_user_id(conn: sqlite3.Connection):
    """Добавляет user_id в read_stats и заливает его из books.

    Миграция идемпотентна: повторный запуск не меняет данные.
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(read_stats)").fetchall()}
    if "user_id" not in columns:
        conn.execute("ALTER TABLE read_stats ADD COLUMN user_id TEXT")

    # Владелец записи статистики — владелец книги; записи удалённых книг остаются NULL.
    conn.execute(
        "UPDATE read_stats "
        "SET user_id = (SELECT user_id FROM books WHERE books.id = read_stats.book_id) "
        "WHERE user_id IS NULL"
    )
    conn.commit()
