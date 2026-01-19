"""Тесты для функциональности изменения прогресса чтения книг."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from telegram import Update, User as TelegramUser, Message, CallbackQuery
from telegram.ext import ContextTypes

import sys
sys.path.insert(0, 'src')

from core.models import Book, User, ReadingStatus
from core.services import BookService
from core.repository import BookRepository
from bot.handlers.book.progress import (
    handle_progress_callback,
    handle_progress_input
)

@pytest.fixture
def mock_update():
    """Создаёт моковый объект Update."""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=TelegramUser)
    update.effective_user.id = 12345
    update.effective_user.username = "test_user"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    return update

@pytest.fixture
def mock_context():
    """Создаёт моковый объект Context."""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context

@pytest.fixture
def mock_book():
    """Создаёт моковую книгу для тестов."""
    return Book(
        id="test-book-id",
        title="Тестовая книга",
        author="Тестовый автор",
        tags=["тест"],
        pages=200,
        current_page=0,
        user_id="user1",
        status=ReadingStatus.WANT_TO_READ
    )

def test_update_book_progress_success():
    """Тестирует успешное обновление прогресса книги через BookService."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get, \
         patch.object(BookRepository, 'update_book') as mock_update:

        test_book = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=0,
            user_id="user1",
            status=ReadingStatus.WANT_TO_READ
        )

        mock_get.return_value = test_book
        mock_update.return_value = test_book

        service = BookService()
        updated_book = service.update_book_progress("test-book-id", 50)

        assert updated_book.current_page == 50
        assert updated_book.status == ReadingStatus.READING
        mock_get.assert_called_once_with("test-book-id")
        mock_update.assert_called_once()
        assert test_book.reading_start_date is not None

def test_update_book_progress_to_completion():
    """Тестирует обновление прогресса до завершения книги."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get, \
         patch.object(BookRepository, 'update_book') as mock_update:

        test_book = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=150,
            user_id="user1",
            status=ReadingStatus.READING
        )

        mock_get.return_value = test_book
        mock_update.return_value = test_book

        service = BookService()
        updated_book = service.update_book_progress("test-book-id", 200)

        assert updated_book.current_page == 200
        assert updated_book.status == ReadingStatus.READ
        assert updated_book.reading_end_date is not None
        mock_update.assert_called_once()

def test_update_book_progress_negative_page():
    """Тестирует обновление прогресса с отрицательной страницей."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get, \
         patch.object(BookRepository, 'update_book') as mock_update:

        test_book = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=50,
            user_id="user1",
            status=ReadingStatus.READING
        )

        mock_get.return_value = test_book
        mock_update.return_value = test_book

        service = BookService()
        updated_book = service.update_book_progress("test-book-id", -10)

        # Страница должна быть ограничена до 0
        assert updated_book.current_page == 0
        mock_update.assert_called_once()

def test_update_book_progress_exceeds_pages():
    """Тестирует обновление прогресса превышающее количество страниц."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get, \
         patch.object(BookRepository, 'update_book') as mock_update:

        test_book = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=50,
            user_id="user1",
            status=ReadingStatus.READING
        )

        mock_get.return_value = test_book
        mock_update.return_value = test_book

        service = BookService()
        updated_book = service.update_book_progress("test-book-id", 300)

        # Страница должна быть ограничена до максимального значения
        assert updated_book.current_page == 200
        # Статус должен измениться на READ при достижении последней страницы
        assert updated_book.status == ReadingStatus.READ
        mock_update.assert_called_once()

def test_update_book_progress_status_change_from_want_to_read():
    """Тестирует изменение статуса с 'Хочу прочитать' на 'Читаю' при обновлении прогресса."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get, \
         patch.object(BookRepository, 'update_book') as mock_update:

        test_book = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=0,
            user_id="user1",
            status=ReadingStatus.WANT_TO_READ
        )

        mock_get.return_value = test_book
        mock_update.return_value = test_book

        service = BookService()
        updated_book = service.update_book_progress("test-book-id", 10)

        assert updated_book.status == ReadingStatus.READING
        assert updated_book.reading_start_date is not None
        mock_update.assert_called_once()

def test_update_book_progress_status_change_to_read():
    """Тестирует изменение статуса на 'Прочитано' при достижении последней страницы."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get, \
         patch.object(BookRepository, 'update_book') as mock_update:

        test_book = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=199,
            user_id="user1",
            status=ReadingStatus.READING
        )

        mock_get.return_value = test_book
        mock_update.return_value = test_book

        service = BookService()
        updated_book = service.update_book_progress("test-book-id", 200)

        assert updated_book.status == ReadingStatus.READ
        assert updated_book.reading_end_date is not None
        mock_update.assert_called_once()

def test_update_book_progress_preserves_reading_start_date():
    """Тестирует сохранение даты начала чтения при обновлении прогресса."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get, \
         patch.object(BookRepository, 'update_book') as mock_update:

        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=1)

        test_book = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=50,
            user_id="user1",
            status=ReadingStatus.READING,
            reading_start_date=start_date
        )

        mock_get.return_value = test_book
        mock_update.return_value = test_book

        service = BookService()
        updated_book = service.update_book_progress("test-book-id", 75)

        # Дата начала должна сохраниться
        assert updated_book.reading_start_date == start_date
        assert updated_book.current_page == 75
        mock_update.assert_called_once()

def test_book_update_progress_method():
    """Тестирует метод update_progress модели Book."""
    book = Book(
        id="test-book-id",
        title="Тестовая книга",
        author="Тестовый автор",
        tags=["тест"],
        pages=200,
        current_page=50,
        user_id="user1"
    )

    # Тестируем обновление с нормальным значением
    book.update_progress(75)
    assert book.current_page == 75

    # Тестируем обновление с отрицательным значением
    book.update_progress(-10)
    assert book.current_page == 0

    # Тестируем обновление с превышающим значением
    book.update_progress(300)
    assert book.current_page == 200

    # Тестируем обновление с нулевым значением
    book.update_progress(0)
    assert book.current_page == 0

def test_update_book_progress_nonexistent_book():
    """Тестирует обновление прогресса для несуществующей книги."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get:
        mock_get.return_value = None

        service = BookService()

        with pytest.raises(ValueError, match="Книга с ID test-book-id не найдена"):
            service.update_book_progress("test-book-id", 50)

def test_handle_progress_callback_initializes_state(mock_update, mock_context, mock_book):
    """Тестирует инициализацию состояния при callback для обновления прогресса."""
    with patch('bot.handlers.book.progress.BookService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_book_by_id.return_value = mock_book

        # Настраиваем мок для callback_query
        mock_update.callback_query = Mock(spec=CallbackQuery)
        mock_update.callback_query.data = "update_progress:test-book-id"

        # Создаём асинхронные мок-методы
        async def mock_edit_message_text(*args, **kwargs):
            return None

        async def mock_reply_text(*args, **kwargs):
            return None

        mock_update.callback_query.edit_message_text = Mock(side_effect=mock_edit_message_text)
        mock_update.callback_query.message = Mock()
        mock_update.callback_query.message.reply_text = Mock(side_effect=mock_reply_text)

        async def run_test():
            await handle_progress_callback(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        assert mock_context.user_data["state"] == "waiting_for_progress_input"
        assert mock_context.user_data["progress_book_id"] == "test-book-id"
        assert mock_context.user_data["progress_book_pages"] == 200
        mock_service.get_book_by_id.assert_called_once_with("test-book-id")

def test_handle_progress_input_success(mock_update, mock_context, mock_book):
    """Тестирует успешный ввод текущей страницы для обновления прогресса."""
    with patch('bot.handlers.book.progress.BookService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.update_book_progress.return_value = mock_book

        # Настраиваем контекст
        mock_context.user_data["progress_book_id"] = "test-book-id"
        mock_context.user_data["progress_book_pages"] = 200

        # Настраиваем мок для сообщения
        mock_update.message = Mock(spec=Message)
        mock_update.message.text = "50"

        async def mock_reply_text(*args, **kwargs):
            return None

        mock_update.message.reply_text = Mock(side_effect=mock_reply_text)

        async def run_test():
            await handle_progress_input(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        mock_service.update_book_progress.assert_called_once_with("test-book-id", 50)
        assert mock_context.user_data == {}
        mock_update.message.reply_text.assert_called_once()

def test_handle_progress_input_invalid_page(mock_update, mock_context):
    """Тестирует ввод некорректной страницы."""
    # Настраиваем контекст
    mock_context.user_data["progress_book_id"] = "test-book-id"
    mock_context.user_data["progress_book_pages"] = 200

    # Настраиваем мок для сообщения
    mock_update.message = Mock(spec=Message)
    mock_update.message.text = "не число"

    async def mock_reply_text(*args, **kwargs):
        return None

    mock_update.message.reply_text = Mock(side_effect=mock_reply_text)

    async def run_test():
        await handle_progress_input(mock_update, mock_context)

    import asyncio
    asyncio.run(run_test())

    mock_update.message.reply_text.assert_called_once()
    # Состояние должно сохраниться
    assert "progress_book_id" in mock_context.user_data

def test_handle_progress_input_negative_page(mock_update, mock_context):
    """Тестирует ввод отрицательной страницы."""
    with patch('bot.handlers.book.progress.BookService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Настраиваем контекст
        mock_context.user_data["progress_book_id"] = "test-book-id"
        mock_context.user_data["progress_book_pages"] = 200

        # Настраиваем мок для сообщения
        mock_update.message = Mock(spec=Message)
        mock_update.message.text = "-10"

        async def mock_reply_text(*args, **kwargs):
            return None

        mock_update.message.reply_text = Mock(side_effect=mock_reply_text)

        async def run_test():
            await handle_progress_input(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        # Должно быть сообщение об ошибке
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Некорректный ввод" in call_args
        assert "отрицательной" in call_args
        # Состояние должно сохраниться
        assert "progress_book_id" in mock_context.user_data

def test_handle_progress_input_exceeds_pages(mock_update, mock_context):
    """Тестирует ввод страницы превышающей количество страниц в книге."""
    with patch('bot.handlers.book.progress.BookService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Настраиваем контекст
        mock_context.user_data["progress_book_id"] = "test-book-id"
        mock_context.user_data["progress_book_pages"] = 200

        # Настраиваем мок для сообщения
        mock_update.message = Mock(spec=Message)
        mock_update.message.text = "300"

        async def mock_reply_text(*args, **kwargs):
            return None

        mock_update.message.reply_text = Mock(side_effect=mock_reply_text)

        async def run_test():
            await handle_progress_input(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        # Должно быть сообщение об ошибке
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Некорректный ввод" in call_args
        assert "200 страниц" in call_args
        # Состояние должно сохраниться
        assert "progress_book_id" in mock_context.user_data

def test_handle_progress_input_zero_page(mock_update, mock_context):
    """Тестирует ввод нулевой страницы."""
    with patch('bot.handlers.book.progress.BookService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.update_book_progress.return_value = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=0,
            user_id="user1"
        )

        # Настраиваем контекст
        mock_context.user_data["progress_book_id"] = "test-book-id"
        mock_context.user_data["progress_book_pages"] = 200

        # Настраиваем мок для сообщения
        mock_update.message = Mock(spec=Message)
        mock_update.message.text = "0"

        async def mock_reply_text(*args, **kwargs):
            return None

        mock_update.message.reply_text = Mock(side_effect=mock_reply_text)

        async def run_test():
            await handle_progress_input(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        mock_service.update_book_progress.assert_called_once_with("test-book-id", 0)
        assert mock_context.user_data == {}
