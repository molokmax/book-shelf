"""Тесты для функциональности изменения статуса книг."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from telegram import Update, User as TelegramUser, Message, CallbackQuery
from telegram.ext import ContextTypes

import sys
sys.path.insert(0, 'src')

from core.models import Book, User, ReadingStatus
from core.services import BookService
from core.repository import BookRepository
from bot.handlers.book.status import handle_status_callback

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

def test_update_book_status_success():
    """Тестирует успешное обновление статуса книги через BookService."""
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
        updated_book = service.update_book_status("test-book-id", "reading")

        assert updated_book.status == ReadingStatus.READING
        mock_get.assert_called_once_with("test-book-id")
        mock_update.assert_called_once()
        assert test_book.updated_at is not None

def test_update_book_status_to_reading_with_zero_page():
    """Тестирует изменение статуса на READING с текущей страницей 0."""
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
        updated_book = service.update_book_status("test-book-id", "reading")

        assert updated_book.status == ReadingStatus.READING
        assert updated_book.reading_start_date is not None
        mock_update.assert_called_once()

def test_update_book_status_to_read_with_full_progress():
    """Тестирует изменение статуса на READ с полным прогрессом."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get, \
         patch.object(BookRepository, 'update_book') as mock_update:

        test_book = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=200,
            user_id="user1",
            status=ReadingStatus.READING
        )

        mock_get.return_value = test_book
        mock_update.return_value = test_book

        service = BookService()
        updated_book = service.update_book_status("test-book-id", "read")

        assert updated_book.status == ReadingStatus.READ
        assert updated_book.reading_end_date is not None
        mock_update.assert_called_once()

def test_update_book_status_to_read_without_full_progress():
    """Тестирует изменение статуса на READ без полного прогресса."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get, \
         patch.object(BookRepository, 'update_book') as mock_update:

        test_book = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=100,
            user_id="user1",
            status=ReadingStatus.READING
        )

        mock_get.return_value = test_book
        mock_update.return_value = test_book

        service = BookService()
        updated_book = service.update_book_status("test-book-id", "read")

        assert updated_book.status == ReadingStatus.READ
        # Дата окончания устанавливается только если текущая страница равна общему количеству страниц
        assert updated_book.reading_end_date is None
        mock_update.assert_called_once()

def test_update_book_status_to_want_to_read():
    """Тестирует изменение статуса на WANT_TO_READ."""
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
        updated_book = service.update_book_status("test-book-id", "want_to_read")

        assert updated_book.status == ReadingStatus.WANT_TO_READ
        mock_update.assert_called_once()

def test_update_book_status_to_postponed():
    """Тестирует изменение статуса на POSTPONED."""
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
        updated_book = service.update_book_status("test-book-id", "postponed")

        assert updated_book.status == ReadingStatus.POSTPONED
        mock_update.assert_called_once()

def test_update_book_status_nonexistent_book():
    """Тестирует обновление статуса для несуществующей книги."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get:
        mock_get.return_value = None

        service = BookService()

        with pytest.raises(ValueError, match="Книга с ID test-book-id не найдена"):
            service.update_book_status("test-book-id", "reading")

def test_update_book_status_preserves_reading_start_date():
    """Тестирует сохранение даты начала чтения при изменении статуса."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get, \
         patch.object(BookRepository, 'update_book') as mock_update:

        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=5)

        test_book = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=100,
            user_id="user1",
            status=ReadingStatus.READING,
            reading_start_date=start_date
        )

        mock_get.return_value = test_book
        mock_update.return_value = test_book

        service = BookService()
        updated_book = service.update_book_status("test-book-id", "reading")

        # Дата начала должна сохраниться
        assert updated_book.reading_start_date == start_date
        assert updated_book.status == ReadingStatus.READING
        mock_update.assert_called_once()

def test_update_book_status_preserves_reading_end_date():
    """Тестирует сохранение даты окончания чтения при изменении статуса."""
    with patch.object(BookRepository, 'get_book_by_id') as mock_get, \
         patch.object(BookRepository, 'update_book') as mock_update:

        from datetime import datetime, timedelta

        end_date = datetime.now() - timedelta(days=1)

        test_book = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=200,
            user_id="user1",
            status=ReadingStatus.READ,
            reading_end_date=end_date
        )

        mock_get.return_value = test_book
        mock_update.return_value = test_book

        service = BookService()
        updated_book = service.update_book_status("test-book-id", "want_to_read")

        # Дата окончания должна сохраниться
        assert updated_book.reading_end_date == end_date
        assert updated_book.status == ReadingStatus.WANT_TO_READ
        mock_update.assert_called_once()

def test_handle_status_callback_select_status(mock_update, mock_context, mock_book):
    """Тестирует обработчик callback для выбора статуса."""
    with patch('bot.handlers.book.status.keyboards') as mock_keyboards:
        # Настраиваем мок для callback_query
        mock_update.callback_query = Mock(spec=CallbackQuery)
        mock_update.callback_query.data = "select_status:test-book-id"

        async def mock_edit_message_text(*args, **kwargs):
            return None

        mock_update.callback_query.edit_message_text = Mock(side_effect=mock_edit_message_text)
        mock_update.callback_query.message = Mock()

        mock_keyboards.status_keyboard.return_value = "mock_keyboard"

        async def run_test():
            await handle_status_callback(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        mock_keyboards.status_keyboard.assert_called_once_with("test-book-id")
        mock_update.callback_query.edit_message_text.assert_called_once()

def test_handle_status_callback_change_status_success(mock_update, mock_context, mock_book):
    """Тестирует успешное изменение статуса через callback."""
    with patch('bot.handlers.book.status.BookService') as mock_service_class, \
         patch('bot.handlers.book.status.get_status_name') as mock_get_status:

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.update_book_status.return_value = mock_book

        mock_get_status.return_value = "Читаю"

        # Настраиваем мок для callback_query
        mock_update.callback_query = Mock(spec=CallbackQuery)
        mock_update.callback_query.data = "change_status:test-book-id:reading"

        async def mock_edit_message_text(*args, **kwargs):
            return None

        async def mock_reply_text(*args, **kwargs):
            return None

        mock_update.callback_query.edit_message_text = Mock(side_effect=mock_edit_message_text)
        mock_update.callback_query.message = Mock()
        mock_update.callback_query.message.reply_text = Mock(side_effect=mock_reply_text)

        async def run_test():
            await handle_status_callback(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        mock_service.update_book_status.assert_called_once_with("test-book-id", "reading")
        mock_get_status.assert_called_once_with(ReadingStatus.WANT_TO_READ)
        mock_update.callback_query.edit_message_text.assert_called_once()
        mock_update.callback_query.message.reply_text.assert_called_once()

def test_handle_status_callback_change_status_error(mock_update, mock_context, mock_book):
    """Тестирует обработку ошибки при изменении статуса."""
    with patch('bot.handlers.book.status.BookService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.update_book_status.side_effect = Exception("Test error")

        # Настраиваем мок для callback_query
        mock_update.callback_query = Mock(spec=CallbackQuery)
        mock_update.callback_query.data = "change_status:test-book-id:reading"

        async def mock_edit_message_text(*args, **kwargs):
            return None

        mock_update.callback_query.edit_message_text = Mock(side_effect=mock_edit_message_text)

        async def run_test():
            await handle_status_callback(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args[0][0]
        assert "Произошла ошибка" in call_args
