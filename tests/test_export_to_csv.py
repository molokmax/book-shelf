import csv
import tempfile
from datetime import datetime

import pytest

from core.models import Book, ReadingStatus
from utils.config import load_config
from utils.export import export_to_csv


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    # Ensure BOT_TOKEN is set for config loading
    monkeypatch.setenv("BOT_TOKEN", "dummy-token")
    # Create a temporary directory for CSV output
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("TEMP_DIR", tmpdir)
        # Patch load_config to use the temporary dir
        original_load = load_config

        def patched_load():
            cfg = original_load()
            cfg.temp_dir = tmpdir
            return cfg

        monkeypatch.setattr("utils.config.load_config", patched_load)
        yield


def make_book(id_, title, author, tags, pages, current_page, status, link, created_at):
    return Book(
        id=id_,
        title=title,
        author=author,
        tags=tags,
        pages=pages,
        current_page=current_page,
        status=status,
        link=link,
        created_at=created_at,
    )


def test_export_to_csv_creates_file_and_writes_correct_content(tmp_path, monkeypatch):
    # Prepare books
    book1 = make_book(
        id_="1",
        title="First Book",
        author="Author A",
        tags=["fiction", "mystery"],
        pages=300,
        current_page=150,
        status=ReadingStatus.READING,
        link="https://example.com/1",
        created_at=datetime(2022, 1, 1, 12, 0, 0),
    )
    book2 = make_book(
        id_="2",
        title="Second Book",
        author="Author B",
        tags=[],
        pages=200,
        current_page=0,
        status=ReadingStatus.WANT_TO_READ,
        link="https://example.com/2",
        created_at=datetime(2022, 2, 2, 15, 30, 0),
    )

    user_id = "user-123"

    csv_path = export_to_csv([book1, book2], user_id)
    # Verify file exists
    assert csv_path.exists()
    # Read CSV content
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        expected_header = [
            "id",
            "title",
            "author",
            "tags",
            "pages",
            "current_page",
            "status",
            "link",
            "created_at",
        ]
        assert header == expected_header
        rows = list(reader)
        assert len(rows) == 2
        # Validate first row
        r1 = rows[0]
        assert r1["id"] == "1"
        assert r1["title"] == "First Book"
        assert r1["author"] == "Author A"
        assert r1["tags"] == "fiction,mystery"
        assert r1["pages"] == "300"
        assert r1["current_page"] == "150"
        assert r1["status"] == ReadingStatus.READING.value
        assert r1["link"] == "https://example.com/1"
        assert r1["created_at"] == book1.created_at.isoformat()
        # Validate second row (no tags)
        r2 = rows[1]
        assert r2["tags"] == ""
        assert r2["status"] == ReadingStatus.WANT_TO_READ.value
