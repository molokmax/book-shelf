"""Тесты для парсера Литрес."""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, "src")

from utils.litres_parser import LitresParserError, is_litres_url, parse_litres_book


@pytest.fixture
def mock_html_content():
    """Возвращает моковый HTML контент страницы книги на Литрес."""
    return """
    <html>
        <head>
            <title>Книга: Тестовая книга - Автор Тестов | Литрес</title>
            <meta property="og:image" content="https://example.com/cover.jpg">
            <meta name="description" content="Описание тестовой книги">
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Book",
                "name": "Тестовая книга",
                "author": {
                    "@type": "Person",
                    "name": "Тестов Автор"
                },
                "numberOfPages": 200,
                "image": "https://example.com/cover.jpg",
                "description": "Описание тестовой книги"
            }
            </script>
        </head>
        <body>
            <div>Автор: <a href="/author/testov">Тестов Автор</a></div>
            <div>Количество страниц: 200</div>
        </body>
    </html>
    """


@pytest.fixture
def mock_html_content_list_authors():
    """Возвращает моковый HTML контент страницы книги на Литрес."""
    return """
    <html>
        <head>
            <title>Книга: Тестовая книга - Автор Тестов | Литрес</title>
            <meta property="og:image" content="https://example.com/cover.jpg">
            <meta name="description" content="Описание тестовой книги">
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Book",
                "name": "Тестовая книга",
                "author": [{
                    "@type": "Person",
                    "name": "Тестов Автор"
                }, {
                    "@type": "Person",
                    "name": "Иванов Иван"
                }],
                "numberOfPages": 200,
                "image": "https://example.com/cover.jpg",
                "description": "Описание тестовой книги"
            }
            </script>
        </head>
        <body>
            <div>Автор: <a href="/author/testov">Тестов Автор</a></div>
            <div>Количество страниц: 200</div>
        </body>
    </html>
    """


def test_is_litres_url_valid():
    """Тестирует проверку валидного URL Литрес."""
    assert is_litres_url("https://www.litres.ru/book/test-123456789") == True
    assert is_litres_url("https://litres.ru/book/test-123456789") == True
    assert is_litres_url("https://www.litres.com/book/test-123456789") == True


def test_is_litres_url_invalid():
    """Тестирует проверку невалидного URL."""
    assert is_litres_url("https://www.ozon.ru/product/test") == False
    assert is_litres_url("https://www.amazon.ru/product/test") == False
    assert is_litres_url("https://example.com/book") == False
    assert is_litres_url("invalid-url") == False


def test_parse_litres_book_success(mock_html_content):
    """Тестирует успешный парсинг книги с Литрес."""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.text = mock_html_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = parse_litres_book("https://www.litres.ru/book/test-123456789")

        assert result["title"] == "Тестовая книга"
        assert result["author"] == "Тестов Автор"
        assert result["pages"] == 200
        assert result["cover_image"] == "https://example.com/cover.jpg"
        assert result["description"] == "Описание тестовой книги"


def test_parse_litres_book_with_several_authors_success(mock_html_content_list_authors):
    """Тестирует успешный парсинг книги с Литрес."""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.text = mock_html_content_list_authors
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = parse_litres_book("https://www.litres.ru/book/test-123456789")

        assert result["title"] == "Тестовая книга"
        assert result["author"] == "Тестов Автор, Иванов Иван"
        assert result["pages"] == 200
        assert result["cover_image"] == "https://example.com/cover.jpg"
        assert result["description"] == "Описание тестовой книги"


def test_parse_litres_book_invalid_url():
    """Тестирует парсинг с невалидным URL."""
    with pytest.raises(LitresParserError) as excinfo:
        parse_litres_book("https://www.ozon.ru/product/test")

    assert "не является ссылкой на Литрес" in str(excinfo.value)


def test_parse_litres_book_missing_title(mock_html_content):
    """Тестирует парсинг с отсутствующим названием книги."""
    html_without_title = mock_html_content.replace(
        '"name": "Тестовая книга",', '"name": "Неизвестное название",'
    )
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.text = html_without_title
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = parse_litres_book("https://www.litres.ru/book/test-123456789")

        assert result["title"] == "Неизвестное название"


def test_parse_litres_book_missing_author(mock_html_content):
    """Тестирует парсинг с отсутствующим автором."""
    html_without_author = mock_html_content.replace(
        '"author": {\n                    "@type": "Person",\n                    "name": "Тестов Автор"\n                },',
        '"author": {},',
    )
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.text = html_without_author
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = parse_litres_book("https://www.litres.ru/book/test-123456789")

        assert result["author"] == "Неизвестный автор"


def test_parse_litres_book_missing_pages(mock_html_content):
    """Тестирует парсинг с отсутствующим количеством страниц."""
    html_without_pages = mock_html_content.replace(
        '"numberOfPages": 200,', '"numberOfPages": null,'
    )
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.text = html_without_pages
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = parse_litres_book("https://www.litres.ru/book/test-123456789")

        assert result["pages"] == 0


def test_parse_litres_book_request_error():
    """Тестирует обработку ошибки запроса."""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection error")

        with pytest.raises(LitresParserError) as excinfo:
            parse_litres_book("https://www.litres.ru/book/test-123456789")

        assert "не удалось распарсить информацию о книге" in str(excinfo.value).lower()


def test_parse_litres_book_http_error():
    """Тестирует обработку HTTP ошибки."""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        with pytest.raises(LitresParserError) as excinfo:
            parse_litres_book("https://www.litres.ru/book/test-123456789")

        assert "не удалось распарсить информацию о книге" in str(excinfo.value).lower()
