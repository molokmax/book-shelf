import ast
import sqlite3
import uuid
from datetime import datetime
from typing import Iterable

from utils import logger
from utils.helpers import normalize_tag_name

log = logger.setup_logger(__name__)


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


def parse_stored_tags(value: str | None) -> list[str]:
    """Парсит старое значение колонки books.tags.

    Исторически данные писались как str(list) (Python-repr) и читались
    через eval, поэтому основной парсер ast.literal_eval, fallback json.
    Повреждённое значение даёт пустой список с предупреждением в лог.
    """
    if value is None:
        return []
    text = value.strip()
    if not text or text == "[]":
        return []

    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        log.warning("Не удалось распарсить теги книги: %s", text[:100])
        return []
    if isinstance(parsed, (list, tuple)):
        return [name for name in (normalize_tag_name(item) for item in parsed) if name]
    log.warning("Неожиданное значение тегов книги: %s", text[:100])
    return []


def resolve_or_create_tags(
    cursor: sqlite3.Cursor,
    user_id: str,
    names: Iterable[str],
) -> list[str]:
    """Гарантирует наличие тегов в справочнике пользователя, возвращает их id.

    Сравнение имён без учёта регистра (str.casefold): SQLite COLLATE NOCASE
    не фолдит кириллицу. Отображаемое имя остаётся в первой введённой форме.
    """
    clean = [name for name in (normalize_tag_name(name) for name in names) if name]
    if not clean:
        return []

    # Уникальность внутри набора с сохранением первой формы имени
    ordered: dict[str, str] = {}
    for name in clean:
        ordered.setdefault(name.casefold(), name)

    known: dict[str, str] = {}
    cursor.execute("SELECT id, name FROM tags WHERE user_id = ?", (user_id,))
    for tag_id, name in cursor.fetchall():
        known.setdefault(name.casefold(), tag_id)

    tag_ids = []
    for key, name in ordered.items():
        tag_id = known.get(key)
        if tag_id is None:
            tag_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO tags (id, user_id, name, created_at) VALUES (?, ?, ?, ?)",
                (tag_id, user_id, name, datetime.now().isoformat()),
            )
            known[key] = tag_id
        tag_ids.append(tag_id)
    return tag_ids


def migrate_books_tags(conn: sqlite3.Connection):
    """Переносит теги из колонки books.tags в tags/book_tags и удаляет колонку.

    Миграция идемпотентна: после удаления колонки повторный запуск не делает
    ничего. Сбои парсинга дают пустой список тегов книги с warning в лог.
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(books)").fetchall()}
    if "tags" not in columns:
        return

    rows = conn.execute("SELECT id, user_id, tags FROM books WHERE tags IS NOT NULL").fetchall()
    for book_id, user_id, raw in rows:
        tag_ids = resolve_or_create_tags(conn.cursor(), user_id, parse_stored_tags(raw))
        if not tag_ids:
            continue
        conn.execute("DELETE FROM book_tags WHERE book_id = ?", (book_id,))
        conn.executemany(
            "INSERT OR IGNORE INTO book_tags (book_id, tag_id) VALUES (?, ?)",
            [(book_id, tag_id) for tag_id in tag_ids],
        )

    try:
        conn.execute("ALTER TABLE books DROP COLUMN tags")
    except sqlite3.OperationalError:
        # Колонку удалить не удалось (старый SQLite), она остаётся мёртвой
        pass
    conn.commit()
