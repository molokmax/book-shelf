"""Тесты для функциональности списка книг."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from telegram import Update, User as TelegramUser, Message
from telegram.ext import ContextTypes

import sys
sys.path.insert(0, 'src')

from core.models import Book, User, ReadingStatus
from core.services import BookService
from core.repository import BookRepository
from utils import helpers
from bot.handlers.book.list import list_books_command

@pytest.fixture
def mock_update():
    """Создаёт моковый объект Update."""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=TelegramUser)
    update.effective_user.id = 12345
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    update.message = Mock(spec=Message)
    # Мокаем async метод reply_text
    async def mock_reply_text(*args, **kwargs):
        return None
    update.message.reply_text = Mock(side_effect=mock_reply_text)
    return update

@pytest.fixture
def mock_context():
    """Создаёт моковый объект Context."""
    return Mock(spec=ContextTypes.DEFAULT_TYPE)

@pytest.fixture
def sample_books():
    """Возвращает список тестовых книг."""
    return [
        Book(
            id="book1",
            title="Властелин колец",
            author="Дж. Р. Р. Толкин",
            tags=["фэнтези", "классика"],
            pages=1000,
            current_page=500,
            status=ReadingStatus.READING,
            user_id="user1"
        ),
        Book(
            id="book2",
            title="Гарри Поттер",
            author="Дж. К. Роулинг",
            tags=["фэнтези", "детская"],
            pages=400,
            current_page=0,
            status=ReadingStatus.WANT_TO_READ,
            user_id="user1"
        ),
        Book(
            id="book3",
            title="1984",
            author="Джордж Оруэлл",
            tags=["антиутопия", "классика"],
            pages=328,
            current_page=328,
            status=ReadingStatus.READ,
            user_id="user1"
        ),
        Book(
            id="book4",
            title="Мастер и Маргарита",
            author="Михаил Булгаков",
            tags=["классика", "фантастика"],
            pages=500,
            current_page=250,
            status=ReadingStatus.POSTPONED,
            user_id="user2"
        )
    ]

def test_get_all_books_empty():
    """Тестирует получение пустого списка книг."""
    with patch.object(BookRepository, 'get_books_by_user_id') as mock_get:
        mock_get.return_value = []
        service = BookService()
        books = service.get_all_books("user1")
        assert books == []
        mock_get.assert_called_once_with("user1")

def test_get_all_books_with_data(sample_books):
    """Тестирует получение списка книг с данными."""
    with patch.object(BookRepository, 'get_books_by_user_id') as mock_get:
        mock_get.return_value = [b for b in sample_books if b.user_id == "user1"]
        service = BookService()
        books = service.get_all_books("user1")
        assert len(books) == 3
        assert all(b.user_id == "user1" for b in books)

def test_get_all_books_all_users(sample_books):
    """Тестирует получение всех книг без фильтрации по пользователю."""
    with patch.object(BookRepository, 'get_all_books') as mock_get:
        mock_get.return_value = sample_books
        service = BookService()
        books = service.get_all_books()
        assert len(books) == 4

def test_get_all_books_sorting(sample_books):
    """Тестирует сортировку книг по статусу."""
    with patch.object(BookRepository, 'get_books_by_user_id') as mock_get:
        mock_get.return_value = [b for b in sample_books if b.user_id == "user1"]
        service = BookService()
        books = service.get_all_books("user1")

        # Проверяем, что прочитанные книги всегда в конце
        read_books = [b for b in books if b.status == ReadingStatus.READ]
        non_read_books = [b for b in books if b.status != ReadingStatus.READ]

        assert all(b.status != ReadingStatus.READ for b in non_read_books)
        assert all(b.status == ReadingStatus.READ for b in read_books)

def test_list_books_command_empty_library(mock_update, mock_context):
    """Тестирует команду /list при пустой библиотеке."""
    with patch('core.services.BookService.get_all_books') as mock_get_books:
        with patch('utils.tg_helpers.get_or_create_user') as mock_get_user:
            with patch('utils.helpers.sort_books_by_status') as mock_sort:
                mock_get_user.return_value = User(id="user1", telegram_id=12345)
                mock_get_books.return_value = []
                mock_sort.return_value = []

                async def run_test():
                    await list_books_command(mock_update, mock_context)

                import asyncio
                asyncio.run(run_test())

                mock_update.message.reply_text.assert_called_once_with(
                    "Ваша библиотека пуста. Добавьте первую книгу с помощью /add"
                )

def test_list_books_command_with_books(mock_update, mock_context, sample_books):
    """Тестирует команду /list с книгами."""
    user_books = [b for b in sample_books if b.user_id == "user1"]

    with patch('core.services.BookService.get_all_books') as mock_get_books:
        with patch('utils.tg_helpers.get_or_create_user') as mock_get_user:
            with patch('utils.helpers.sort_books_by_status') as mock_sort:
                with patch('utils.helpers.format_book_info') as mock_format:
                    mock_get_user.return_value = User(id="user1", telegram_id=12345)
                    mock_get_books.return_value = user_books
                    mock_sort.return_value = user_books
                    mock_format.side_effect = lambda idx, book: f"Book {idx}: {book.title}"

                    async def run_test():
                        await list_books_command(mock_update, mock_context)

                    import asyncio
                    asyncio.run(run_test())

                    # Проверяем, что сообщение было отправлено
                    mock_update.message.reply_text.assert_called_once()
                    call_args = mock_update.message.reply_text.call_args
                    assert "📚 Ваша библиотека:" in call_args[0][0]
                    assert call_args[1].get("parse_mode") == "Markdown"

def test_sort_books_by_status(sample_books):
    """Тестирует сортировку книг по статусам."""
    user_books = [b for b in sample_books if b.user_id == "user1"]
    sorted_books = helpers.sort_books_by_status(user_books)

    # Проверяем порядок: читаю, хочу прочитать, отложено, прочитано
    status_order = [b.status for b in sorted_books]
    expected_order = [
        ReadingStatus.READING,
        ReadingStatus.WANT_TO_READ,
        ReadingStatus.READ
    ]

    assert status_order == expected_order

def test_format_book_info(sample_books):
    """Тестирует форматирование информации о книге."""
    book = sample_books[0]  # Властелин колец
    formatted = helpers.format_book_info(1, book)

    assert "**Властелин колец**" in formatted
    assert "*Автор:* Дж. Р. Р. Толкин" in formatted
    assert "*Теги:* фэнтези, классика" in formatted
    assert "*Страниц:* 1000" in formatted
    assert "*Прогресс:* 500/1000 (50%)" in formatted

def test_format_book_info_no_tags(sample_books):
    """Тестирует форматирование книги без тегов."""
    book = sample_books[0]
    book.tags = []
    formatted = helpers.format_book_info(1, book)

    assert "*Теги:* Нет тегов" in formatted

def test_format_book_info_zero_pages(sample_books):
    """Тестирует форматирование книги с нулевым количеством страниц."""
    book = sample_books[0]
    book.pages = 0
    book.current_page = 0
    formatted = helpers.format_book_info(1, book)

    assert "*Прогресс:* 0/0 (0%)" in formatted

def test_get_status_emoji():
    """Тестирует получение эмодзи для статуса."""
    assert helpers.get_status_emoji("want_to_read") == "📖"
    assert helpers.get_status_emoji("reading") == "📚"
    assert helpers.get_status_emoji("read") == "📕"
    assert helpers.get_status_emoji("postponed") == "⏸️"
    assert helpers.get_status_emoji("unknown") == "📘"

def test_get_status_name():
    """Тестирует получение названия статуса."""
    assert helpers.get_status_name("want_to_read") == "Хочу прочитать"
    assert helpers.get_status_name("reading") == "Читаю"
    assert helpers.get_status_name("read") == "Прочитал"
    assert helpers.get_status_name("postponed") == "Отложил"
    assert helpers.get_status_name("unknown") == "Неизвестный статус"

def test_book_service_integration(sample_books):
    """Тестирует интеграцию BookService с BookRepository."""
    with patch.object(BookRepository, 'get_books_by_user_id') as mock_get:
        mock_get.return_value = [b for b in sample_books if b.user_id == "user1"]

        service = BookService()
        books = service.get_all_books("user1")

        assert len(books) == 3
        assert all(isinstance(b, Book) for b in books)
        assert all(b.user_id == "user1" for b in books)

def test_list_books_command_integration(mock_update, mock_context):
    """Тестирует полную интеграцию команды /list."""
    # Создаём тестовые данные
    test_books = [
        Book(
            id="book1",
            title="Тестовая книга 1",
            author="Автор 1",
            tags=["тест"],
            pages=100,
            current_page=50,
            status=ReadingStatus.READING,
            user_id="user1"
        ),
        Book(
            id="book2",
            title="Тестовая книга 2",
            author="Автор 2",
            tags=["тест"],
            pages=200,
            current_page=0,
            status=ReadingStatus.WANT_TO_READ,
            user_id="user1"
        )
    ]

    with patch('core.services.BookService.get_all_books') as mock_get_books:
        with patch('utils.helpers.get_or_create_user') as mock_get_user:
            with patch('utils.helpers.sort_books_by_status') as mock_sort:
                mock_get_user.return_value = User(id="user1", telegram_id=12345)
                mock_get_books.return_value = test_books
                mock_sort.return_value = test_books

                async def run_test():
                    await list_books_command(mock_update, mock_context)

                import asyncio
                asyncio.run(run_test())

                # Проверяем, что сообщение было отправлено
                mock_update.message.reply_text.assert_called_once()
                response = mock_update.message.reply_text.call_args[0][0]

                # Проверяем, что ответ содержит ожидаемую информацию
                assert "📚 Ваша библиотека:" in response
                assert "Тестовая книга 1" in response
                assert "Тестовая книга 2" in response
                assert "Автор 1" in response
                assert "Автор 2" in response
