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
    handle_add_book_pages,
    handle_add_method_callback,
    handle_add_book_from_litres,
    handle_confirm_litres_book,
    handle_litres_book_tags
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
    with patch('utils.tg_helpers.get_or_create_user') as mock_get_user:
        mock_get_user.return_value = User(id="user1", external_id=12345)

        async def run_test():
            await add_book_command(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        assert mock_context.user_data["state"] == "selecting_add_method"
        assert mock_context.user_data["user_id"] == "user1"
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "📖 Добавление новой книги" in call_args[0][0]
        assert "Пожалуйста, выберите способ добавления книги:" in call_args[0][0]

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

def test_add_method_callback_manual(mock_update, mock_context):
    """Тестирует обработчик выбора метода добавления (ручной ввод)."""
    from telegram import CallbackQuery

    # Создаём моковый callback query
    mock_query = Mock(spec=CallbackQuery)
    mock_query.data = "add_method:manual"
    mock_query.message = mock_update.message
    # Мокаем async метод edit_message_text
    async def mock_edit_message_text(*args, **kwargs):
        return None
    mock_query.edit_message_text = Mock(side_effect=mock_edit_message_text)

    mock_update.callback_query = mock_query

    mock_context.user_data["state"] = "selecting_add_method"
    mock_context.user_data["user_id"] = "user1"

    async def run_test():
        await handle_add_method_callback(mock_update, mock_context)

    import asyncio
    asyncio.run(run_test())

    assert mock_context.user_data["state"] == "waiting_for_title"
    # Проверяем оба вызова: edit_message_text и reply_text
    mock_query.edit_message_text.assert_called_once()
    edit_call_args = mock_query.edit_message_text.call_args
    assert "📖 Добавление новой книги" in edit_call_args[0][0]

    mock_query.message.reply_text.assert_called_once()
    reply_call_args = mock_query.message.reply_text.call_args
    assert "Пожалуйста, введите название книги:" in reply_call_args[0][0]

def test_book_creation_integration(mock_update, mock_context):
    """Тестирует полный цикл создания книги."""
    from telegram import CallbackQuery

    with patch('utils.tg_helpers.get_or_create_user') as mock_get_user:
        with patch('bot.handlers.book.add.BookService') as mock_service_class:
            mock_get_user.return_value = User(id="user1", external_id=12345)

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

            # Создаём моковый callback query для выбора метода
            mock_query = Mock(spec=CallbackQuery)
            mock_query.data = "add_method:manual"
            mock_query.message = mock_update.message
            # Мокаем async метод edit_message_text
            async def mock_edit_message_text(*args, **kwargs):
                return None
            mock_query.edit_message_text = Mock(side_effect=mock_edit_message_text)
            mock_update.callback_query = mock_query

            # Шаг 1: Команда /add
            async def run_add_command():
                await add_book_command(mock_update, mock_context)

            async def run_method_callback():
                await handle_add_method_callback(mock_update, mock_context)

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
            asyncio.run(run_method_callback())

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

def test_add_method_callback_litres(mock_update, mock_context):
    """Тестирует обработчик выбора метода добавления (Литрес)."""
    from telegram import CallbackQuery

    # Создаём моковый callback query
    mock_query = Mock(spec=CallbackQuery)
    mock_query.data = "add_method:litres"
    mock_query.message = mock_update.message
    # Мокаем async метод edit_message_text
    async def mock_edit_message_text(*args, **kwargs):
        return None
    mock_query.edit_message_text = Mock(side_effect=mock_edit_message_text)
    # Мокаем async метод answer
    async def mock_answer(*args, **kwargs):
        return None
    mock_query.answer = Mock(side_effect=mock_answer)

    mock_update.callback_query = mock_query

    mock_context.user_data["state"] = "selecting_add_method"
    mock_context.user_data["user_id"] = "user1"

    async def run_test():
        await handle_add_method_callback(mock_update, mock_context)

    import asyncio
    asyncio.run(run_test())

    assert mock_context.user_data["state"] == "waiting_for_litres_url"
    # Проверяем оба вызова: edit_message_text и reply_text
    mock_query.edit_message_text.assert_called_once()
    edit_call_args = mock_query.edit_message_text.call_args
    assert "🔗 Добавление книги из Литрес" in edit_call_args[0][0]

    mock_query.message.reply_text.assert_called_once()
    reply_call_args = mock_query.message.reply_text.call_args
    assert "Пожалуйста, введите ссылку на книгу с Литрес:" in reply_call_args[0][0]

def test_handle_add_book_from_litres_success(mock_update, mock_context):
    """Тестирует успешный обработчик ссылки на книгу из Литрес."""
    from utils.litres_parser import parse_litres_book

    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["state"] = "waiting_for_litres_url"
    mock_update.message.text = "https://www.litres.ru/book/test-123456789"

    with patch('bot.handlers.book.add.parse_litres_book') as mock_parse:
        mock_parse.return_value = {
            'title': 'Тестовая книга',
            'author': 'Тестовый автор',
            'pages': 200,
            'cover_image': 'https://example.com/cover.jpg',
            'description': 'Описание тестовой книги'
        }

        async def run_test():
            await handle_add_book_from_litres(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        assert mock_context.user_data["book_title"] == "Тестовая книга"
        assert mock_context.user_data["book_author"] == "Тестовый автор"
        assert mock_context.user_data["book_pages"] == 200
        assert mock_context.user_data["book_cover"] == "https://example.com/cover.jpg"
        assert mock_context.user_data["state"] == "confirming_litres_book"
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "📖 Нашли книгу на Литрес!" in response
        assert "Тестовая книга" in response
        assert "Тестовый автор" in response
        assert "200" in response

def test_handle_add_book_from_litres_missing_required(mock_update, mock_context):
    """Тестирует обработчик с отсутствующими обязательными параметрами."""
    from utils.litres_parser import LitresParserError

    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["state"] = "waiting_for_litres_url"
    mock_update.message.text = "https://www.litres.ru/book/test-123456789"

    with patch('bot.handlers.book.add.parse_litres_book') as mock_parse:
        mock_parse.side_effect = LitresParserError("Не удалось получить обязательные параметры книги")

        async def run_test():
            await handle_add_book_from_litres(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "❌ Ошибка при получении информации о книге" in response
        assert mock_context.user_data["state"] == "waiting_for_litres_url"

def test_handle_add_book_from_litres_invalid_url(mock_update, mock_context):
    """Тестирует обработчик с невалидной ссылкой."""
    from utils.litres_parser import LitresParserError

    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["state"] = "waiting_for_litres_url"
    mock_update.message.text = "https://www.ozon.ru/product/test"

    with patch('bot.handlers.book.add.parse_litres_book') as mock_parse:
        mock_parse.side_effect = LitresParserError("URL не является ссылкой на Литрес")

        async def run_test():
            await handle_add_book_from_litres(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "❌ Ошибка при получении информации о книге" in response
        assert "не является ссылкой на Литрес" in response

def test_handle_confirm_litres_book_confirm(mock_update, mock_context):
    """Тестирует подтверждение добавления книги из Литрес."""
    from telegram import CallbackQuery

    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["book_title"] = "Тестовая книга"
    mock_context.user_data["book_author"] = "Тестовый автор"
    mock_context.user_data["book_pages"] = 200

    # Создаём моковый callback query
    mock_query = Mock(spec=CallbackQuery)
    mock_query.data = "confirm_add:confirm"
    mock_query.message = mock_update.message
    # Мокаем async метод edit_message_text
    async def mock_edit_message_text(*args, **kwargs):
        return None
    mock_query.edit_message_text = Mock(side_effect=mock_edit_message_text)

    mock_update.callback_query = mock_query

    async def run_test():
        await handle_confirm_litres_book(mock_update, mock_context)

    import asyncio
    asyncio.run(run_test())

    # После подтверждения должен быть запрос тегов
    assert mock_context.user_data["state"] == "waiting_for_litres_tags"
    mock_query.edit_message_text.assert_called_once()
    response = mock_query.edit_message_text.call_args[0][0]
    assert "введите теги книги" in response

def test_handle_confirm_litres_book_cancel(mock_update, mock_context):
    """Тестирует отмену добавления книги из Литрес."""
    from telegram import CallbackQuery

    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["book_title"] = "Тестовая книга"
    mock_context.user_data["book_author"] = "Тестовый автор"
    mock_context.user_data["book_pages"] = 200

    # Создаём моковый callback query
    mock_query = Mock(spec=CallbackQuery)
    mock_query.data = "confirm_add:cancel"
    mock_query.message = mock_update.message
    # Мокаем async метод edit_message_text
    async def mock_edit_message_text(*args, **kwargs):
        return None
    mock_query.edit_message_text = Mock(side_effect=mock_edit_message_text)

    mock_update.callback_query = mock_query

    async def run_test():
        await handle_confirm_litres_book(mock_update, mock_context)

    import asyncio
    asyncio.run(run_test())

    assert mock_context.user_data == {}
    mock_query.edit_message_text.assert_called_once()
    response = mock_query.edit_message_text.call_args[0][0]
    assert "❌ Добавление книги отменено" in response

def test_handle_litres_book_tags(mock_update, mock_context):
    """Тестирует обработчик тегов книги из Литрес."""
    mock_context.user_data["user_id"] = "user1"
    mock_context.user_data["state"] = "waiting_for_litres_tags"
    mock_context.user_data["book_title"] = "Тестовая книга"
    mock_context.user_data["book_author"] = "Тестовый автор"
    mock_context.user_data["book_pages"] = 200
    mock_update.message.text = "тест, litres, книга"

    with patch('bot.handlers.book.add.BookService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_book.return_value = Book(
            id="new-book-id",
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест", "litres", "книга"],
            pages=200,
            user_id="user1"
        )

        async def run_test():
            await handle_litres_book_tags(mock_update, mock_context)

        import asyncio
        asyncio.run(run_test())

        mock_service.create_book.assert_called_once_with(
            title="Тестовая книга",
            author="Тестовый автор",
            tags=["тест", "litres", "книга"],
            pages=200,
            user_id="user1"
        )
        assert mock_context.user_data == {}
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "Книга 'Тестовая книга' успешно добавлена" in response
