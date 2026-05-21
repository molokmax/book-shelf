import csv
import time
from pathlib import Path
from typing import List

from core.models import Book
from utils.config import load_config


def export_to_csv(books: List[Book], user_id: str) -> Path:
    """Экспортирует список книг в CSV‑файл."""
    config = load_config()
    dir = Path(config.temp_dir)
    dir.mkdir(parents=True, exist_ok=True)
    csv_path = dir / f"{user_id}_{int(time.time())}.csv"

    fieldnames = [
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

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for book in books:
            writer.writerow(
                {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "tags": ",".join(book.tags),
                    "pages": book.pages,
                    "current_page": book.current_page,
                    "status": book.status.value,
                    "link": book.link,
                    "created_at": book.created_at.isoformat(),
                }
            )
    return csv_path
