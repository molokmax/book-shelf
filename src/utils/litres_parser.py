"""Утилиты для парсинга книг с Литрес."""

import json
import re
from typing import Dict
from urllib.parse import urlparse

import requests

from utils import logger

log = logger.setup_logger(__name__)


class LitresParserError(Exception):
    """Исключение для ошибок парсинга Литрес."""

    pass


def is_litres_url(url: str) -> bool:
    """Проверяет, является ли URL ссылкой на Литрес."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.endswith("litres.ru") or parsed.netloc.endswith("litres.com")
    except Exception as e:
        log.warning(f"Возникла ошибка при разборе ссылки: {e}")
        return False


def parse_litres_book(url: str) -> Dict:
    """
    Парсит информацию о книге с Литрес по ссылке.

    Args:
        url: URL страницы книги на Литрес

    Returns:
        Словарь с информацией о книге:
        {
            'title': str,  # Название книги
            'author': str,  # Автор
            'pages': int,  # Количество страниц
            'cover_image': str,  # URL обложки (опционально)
            'description': str  # Описание (опционально)
        }

    Raises:
        LitresParserError: Если не удалось получить информацию о книге
    """
    if not is_litres_url(url):
        raise LitresParserError("URL не является ссылкой на Литрес")

    try:
        # Отправляем GET запрос к странице книги
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        html_content = response.text

        # Ищем JSON-LD элемент с информацией о книге
        json_ld_match = re.search(
            r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
            html_content,
            re.DOTALL,
        )

        if not json_ld_match:
            raise json.JSONDecodeError("JSON-LD не найден")

        # Извлекаем JSON и парсим его
        json_str = json_ld_match.group(1).strip()

        data = json.loads(json_str)

        # Проверяем, что это Book объект
        if data.get("@type") != "Book":
            # Попробуем найти другой JSON-LD элемент
            raise json.JSONDecodeError("JSON-LD не содержит Book данные")

        # Извлекаем информацию из JSON-LD
        title = data.get("name", "Неизвестное название")
        if isinstance(data.get("author"), dict):
            author = data.get("author", {}).get("name", "Неизвестный автор")
        elif isinstance(data.get("author"), list):
            authors = data.get("author", [])
            author = ", ".join(x.get("name", "Неизвестный автор") for x in authors)
        else:
            author = "Неизвестный автор"
        pages = data.get("numberOfPages", 0)
        cover_image = data.get("image")
        description = data.get("description")

        return {
            "title": title,
            "author": author,
            "pages": int(pages) if pages else 0,
            "cover_image": cover_image,
            "description": description,
        }

    except requests.RequestException as e:
        log.error(f"Ошибка при запросе к Литрес: {e}")
        raise LitresParserError(f"Не удалось загрузить страницу: {e}")
    except json.JSONDecodeError as e:
        log.error(f"Ошибка при парсинге JSON-LD: {e}")
        raise LitresParserError(f"Не удалось распарсить информацию о книге: {e}")
    except Exception as e:
        log.error(f"Ошибка при парсинге страницы Литрес: {e}")
        raise LitresParserError(f"Не удалось распарсить информацию о книге: {e}")
