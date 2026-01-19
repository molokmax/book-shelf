"""Тесты для функциональности добавления книг."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from telegram import Update, User as TelegramUser, Message
from telegram.ext import ContextTypes

import sys
sys.path.insert(0, 'src')

from core.models import Book, User, ReadingStatus
from core.services import BookService
from core.repository import BookRepository
from utils import helpers
from bot.handlers.book.add import (
    add_book_command,
    handle_add_book_title,
    handle_add_book_author,
    handle_add_book_tags,
    handle_add_book_pages
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
    update.message = Mock(spec=Message)
    # Мокаем async метод reply_text
    async def mock_reply_text(*args, **kwargs):
        return None
    update.message.reply_text = Mock(side_effect=mock_reply_text)
    # Мокаем текст сообщения
    update.message.text = "Тестовая книга"
    return update

@pytest.fixture
def mock_context():
    """Создаёт моковый объект Context."""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context

def test_create_book_success():
    """Тестирует успешное создание книги через BookService."""
    with patch.object(BookRepository, 'add_book') as mock_add:
        mock_add.return_value = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест", "книга"],
            pages=200,
            user_id="user1"
        )

        service = BookService()
        book = service.create_book(
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест", "книга"],
            pages=200,
            user_id="user1"
        )

        assert book.title == "Тестовая книга"
        assert book.author == "Тестовый автор"
        assert book.tags == ["тест", "книга"]
        assert book.pages == 200
        assert book.user_id == "user1"
        assert book.status == ReadingStatus.WANT_TO_READ
        assert book.current_page == 0
        mock_add.assert_called_once()

def test_create_book_with_custom_status():
    """Тестирует создание книги с пользовательским статусом."""
    with patch.object(BookRepository, 'add_book') as mock_add:
        mock_add.return_value = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=100,
            user_id="user1",
            status=ReadingStatus.READING
        )

        service = BookService()
        book = service.create_book(
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=100,
            user_id="user1",
            status="reading"
        )

        assert book.status == ReadingStatus.READING
        mock_add.assert_called_once()

def test_create_book_with_custom_page():
    """Тестирует создание книги с пользовательской текущей страницей."""
    with patch.object(BookRepository, 'add_book') as mock_add:
        mock_add.return_value = Book(
            id="test-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            current_page=50,
            user_id="user1"
        )

        service = BookService()
        book = service.create_book(
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест"],
            pages=200,
            user_id="user1",
            current_page=50
        )

        assert book.current_page == 50
        mock_add.assert_called_once()

def test_add_book_command_initializes_state(mock_update, mock_context):
    """Тестирует инициализацию состояния при команде /add."""
    with patch('utils.helpers.get_or_create_user') as mock_get_user:
        mock_get_user.return_value = User(id="user1", telegram_id=12345)

        async def run_test():
            await add_book_command(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        assert mock_context.user_data["state"] == "waiting_for_title"
        assert mock_context.user_data["user_id"] == "user1"
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "📖 Добавление новой книги" in call_args[0][0]
        assert "Пожалуйста, введите название книги:" in call_args[0][0]

def test_handle_add_book_title(mock_update, mock_context):
    """Тестирует обработчик названия книги."""
    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["state"] = "waiting_for_title"
    mock_update.message.text = "Тестовая книга"

    async def run_test():
        await handle_add_book_title(mock_update, mock_context)

    import asyncio
    asyncio.run(run_test())

    assert mock_context.user_data["book_title"] == "Тестовая книга"
    assert mock_context.user_data["state"] == "waiting_for_author"
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "Отлично! Теперь введите автора книги:" in call_args[0][0]

def test_handle_add_book_author(mock_update, mock_context):
    """Тестирует обработчик автора книги."""
    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["state"] = "waiting_for_author"
    mock_context.user_data["book_title"] = "Тестовая книга"
    mock_update.message.text = "Тестовый автор"

    async def run_test():
        await handle_add_book_author(mock_update, mock_context)

    import asyncio
    asyncio.run(run_test())

    assert mock_context.user_data["book_author"] == "Тестовый автор"
    assert mock_context.user_data["state"] == "waiting_for_tags"
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "Хорошо! Теперь введите теги книги" in call_args[0][0]

def test_handle_add_book_tags(mock_update, mock_context):
    """Тестирует обработчик тегов книги."""
    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["state"] = "waiting_for_tags"
    mock_context.user_data["book_title"] = "Тестовая книга"
    mock_context.user_data["book_author"] = "Тестовый автор"
    mock_update.message.text = "тест, книга"

    async def run_test():
        await handle_add_book_tags(mock_update, mock_context)

    import asyncio
    asyncio.run(run_test())

    assert mock_context.user_data["book_tags"] == ["тест", "книга"]
    assert mock_context.user_data["state"] == "waiting_for_pages"
    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "Отлично! Теперь введите количество страниц" in call_args[0][0]

def test_handle_add_book_tags_empty(mock_update, mock_context):
    """Тестирует обработчик тегов с пустыми тегами."""
    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["state"] = "waiting_for_tags"
    mock_context.user_data["book_title"] = "Тестовая книга"
    mock_context.user_data["book_author"] = "Тестовый автор"
    mock_update.message.text = ",,  ,"

    async def run_test():
        await handle_add_book_tags(mock_update, mock_context)

    import asyncio
    asyncio.run(run_test())

    assert mock_context.user_data["book_tags"] == []
    assert mock_context.user_data["state"] == "waiting_for_pages"

def test_handle_add_book_pages_success(mock_update, mock_context):
    """Тестирует успешный обработчик количества страниц."""
    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["state"] = "waiting_for_pages"
    mock_context.user_data["book_title"] = "Тестовая книга"
    mock_context.user_data["book_author"] = "Тестовый автор"
    mock_context.user_data["book_tags"] = ["тест", "книга"]
    mock_update.message.text = "200"

    with patch('bot.handlers.book.add.BookService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_book.return_value = Book(
            id="new-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест", "книга"],
            pages=200,
            user_id="user1"
        )

        async def run_test():
            await handle_add_book_pages(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        mock_service.create_book.assert_called_once_with(
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест", "книга"],
            pages=200,
            user_id="user1"
        )
        assert mock_context.user_data == {}
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "Книга 'Тестовая книга' успешно добавлена" in response

def test_handle_add_book_pages_invalid(mock_update, mock_context):
    """Тестирует обработчик с недопустимым количеством страниц."""
    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["state"] = "waiting_for_pages"
    mock_context.user_data["book_title"] = "Тестовая книга"
    mock_context.user_data["book_author"] = "Тестовый автор"
    mock_context.user_data["book_tags"] = ["тест"]
    mock_update.message.text = "-10"

    async def run_test():
        await handle_add_book_pages(mock_update, mock_context)

    import asyncio
    try:
        asyncio.run(run_test())
        assert False, "Должно быть thrown ValueError"
    except ValueError:
        pass

def test_handle_add_book_pages_zero(mock_update, mock_context):
    """Тестирует обработчик с нулевым количеством страниц."""
    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["state"] = "waiting_for_pages"
    mock_context.user_data["book_title"] = "Тестовая книга"
    mock_context.user_data["book_author"] = "Тестовый автор"
    mock_context.user_data["book_tags"] = ["тест"]
    mock_update.message.text = "0"

    async def run_test():
        await handle_add_book_pages(mock_update, mock_context)

    import asyncio
    try:
        asyncio.run(run_test())
        assert False, "Должно быть thrown ValueError"
    except ValueError:
        pass

def test_book_creation_integration(mock_update, mock_context):
    """Тестирует полный цикл создания книги."""
    with patch('utils.helpers.get_or_create_user') as mock_get_user:
        with patch('bot.handlers.book.add.BookService') as mock_service_class:
            mock_get_user.return_value = User(id="user1", telegram_id=12345)

            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.create_book.return_value = Book(
                id="new-book-id",
                title="Интеграционная книга",
                author="Интеграционный автор",
                tags=["интеграция", "тест"],
                pages=300,
                user_id="user1"
            )

            # Шаг 1: Команда /add
            async def run_add_command():
                await add_book_command(mock_update, mock_context)

            async def run_title():
                await handle_add_book_title(mock_update, mock_context)

            async def run_author():
                await handle_add_book_author(mock_update, mock_context)

            async def run_tags():
                await handle_add_book_tags(mock_update, mock_context)

            async def run_pages():
                await handle_add_book_pages(mock_update, mock_context)

            import asyncio
            asyncio.run(run_add_command())

            mock_update.message.text = "Интеграционная книга"
            asyncio.run(run_title())

            mock_update.message.text = "Интеграционный автор"
            asyncio.run(run_author())

            mock_update.message.text = "интеграция, тест"
            asyncio.run(run_tags())

            mock_update.message.text = "300"
            asyncio.run(run_pages())

            mock_service.create_book.assert_called_once_with(
                title="Интеграционная книга",
                author="Интеграционный автор",
                tags=["интеграция", "тест"],
                pages=300,
                user_id="user1"
            )
            assert mock_context.user_data == {}
