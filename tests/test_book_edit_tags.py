"""Тесты для редактирования тэгов книги."""

import pytest
import sys
sys.path.insert(0, 'src')

from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, CallbackQuery, User
from telegram.ext import ContextTypes
from datetime import datetime

from core.models import Book, ReadingStatus
from core.services import BookService
from bot.handlers.book.edit import handle_edit_callback, handle_edit_tags_message
from bot.keyboards import main as keyboards

@pytest.fixture
def book_service():
    """Фикстура для BookService."""
    with patch('core.services.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        return BookService()

@pytest.fixture
def sample_book():
    """Фикстура для тестовой книги."""
    return Book(
        id="test-book-1",
        title="Тестовая книга",
        author="Тестовый автор",
        tags=["фантастика", "наука"],
        pages=300,
        current_page=50,
        status=ReadingStatus.READING,
        user_id="user-1"
    )

@pytest.mark.asyncio
async def test_update_book_tags_success(book_service, sample_book):
    """Тест успешного обновления тэгов книги."""
    from datetime import datetime, timedelta
    
    # Создаем копию книги с обновленным временем
    updated_book = sample_book.__class__(**{k: v for k, v in sample_book.__dict__.items()})
    updated_book.tags = ["фантастика", "наука", "приключения"]
    updated_book.updated_at = sample_book.updated_at + timedelta(seconds=1)
    
    # Моким репозиторий
    book_service.book_repo.get_book_by_id = MagicMock(return_value=sample_book)
    book_service.book_repo.update_book = MagicMock(return_value=updated_book)

    # Обновляем тэги
    new_tags = ["фантастика", "наука", "приключения"]
    result = book_service.update_book_tags("test-book-1", new_tags)

    # Проверяем, что метод был вызван
    book_service.book_repo.get_book_by_id.assert_called_once_with("test-book-1")
    book_service.book_repo.update_book.assert_called_once()

    # Проверяем, что тэги обновлены
    assert result.tags == new_tags
    assert result.updated_at > sample_book.updated_at

@pytest.mark.asyncio
async def test_update_book_tags_nonexistent_book(book_service):
    """Тест обновления тэгов несуществующей книги."""
    book_service.book_repo.get_book_by_id = MagicMock(return_value=None)

    with pytest.raises(ValueError, match="Книга с ID test-book-1 не найдена"):
        book_service.update_book_tags("test-book-1", ["новый", "тег"])

@pytest.mark.asyncio
async def test_handle_edit_tags_callback(sample_book):
    """Тест обработчика callback для редактирования тэгов."""
    from src.bot.keyboards.main import cancel_inline_keyboard
    
    # Мокируем BookService и его методы
    with patch('bot.handlers.book.edit.BookService') as mock_book_service_class:
        mock_book_service_instance = MagicMock()
        mock_book_service_instance.get_book_by_id.return_value = sample_book
        mock_book_service_class.return_value = mock_book_service_instance

        # Создаём мок для Update
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = "edit_tags:test-book-1"
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.answer = AsyncMock()

        # Создаём мок для контекста
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        # Вызываем обработчик
        await handle_edit_callback(update, context)

        # Проверяем, что сообщение было отправлено
        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        message_text = call_args[0][0]
        reply_markup = call_args[1].get('reply_markup')

        # Проверяем, что в сообщении указаны текущие тэги
        assert "фантастика, наука" in message_text
        assert "отправьте" in message_text.lower() or "нажмите" in message_text.lower()

        # Проверяем, что клавиатура отмены была передана
        assert reply_markup is not None

        # Проверяем, что состояние сохранено
        assert context.user_data["edit_state"] == "editing_tags"
        assert context.user_data["selected_book_id"] == "test-book-1"
        
        # Проверяем, что BookService был создан
        mock_book_service_class.assert_called_once()
        # Проверяем, что был вызван метод get_book_by_id
        mock_book_service_instance.get_book_by_id.assert_called_once_with("test-book-1")

@pytest.mark.asyncio
async def test_handle_edit_tags_message_success(sample_book):
    """Тест обработчика сообщения с новыми тэгами."""
    from datetime import timedelta
    
    # Создаем копию книги с обновленными тегами
    updated_book = sample_book.__class__(**{k: v for k, v in sample_book.__dict__.items()})
    updated_book.tags = ["фантастика", "наука", "приключения"]
    updated_book.updated_at = sample_book.updated_at + timedelta(seconds=1)
    
    # Мокируем BookService и его методы
    with patch('bot.handlers.book.edit.BookService') as mock_book_service_class:
        mock_book_service_instance = MagicMock()
        mock_book_service_instance.get_book_by_id.return_value = sample_book
        mock_book_service_instance.update_book_tags.return_value = updated_book
        mock_book_service_class.return_value = mock_book_service_instance

        # Создаём мок для Update
        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "фантастика, наука, приключения"
        update.message.reply_text = AsyncMock()

        # Создаём мок для контекста
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {
            "edit_state": "editing_tags",
            "selected_book_id": "test-book-1"
        }

        # Вызываем обработчик
        await handle_edit_tags_message(update, context)

        # Проверяем, что сообщение было отправлено
        update.message.reply_text.assert_called_once()
        message_text = update.message.reply_text.call_args[0][0]

        # Проверяем, что в сообщении указано об успешном обновлении
        assert "Тэги книги успешно обновлены" in message_text
        assert "фантастика, наука, приключения" in message_text
        
        # Проверяем, что BookService был создан
        mock_book_service_class.assert_called_once()
        # Проверяем, что были вызваны нужные методы
        mock_book_service_instance.get_book_by_id.assert_called_once_with("test-book-1")
        mock_book_service_instance.update_book_tags.assert_called_once_with("test-book-1", ["фантастика", "наука", "приключения"])

    # Проверяем, что состояние сброшено
    assert context.user_data == {}

@pytest.mark.asyncio
async def test_handle_edit_tags_message_empty_tags(sample_book):
    """Тест обработчика сообщения с пустыми тэгами."""
    from datetime import timedelta
    
    # Создаем копию книги с пустыми тегами
    updated_book = sample_book.__class__(**{k: v for k, v in sample_book.__dict__.items()})
    updated_book.tags = []
    updated_book.updated_at = sample_book.updated_at + timedelta(seconds=1)
    
    # Мокируем BookService и его методы
    with patch('bot.handlers.book.edit.BookService') as mock_book_service_class:
        mock_book_service_instance = MagicMock()
        mock_book_service_instance.get_book_by_id.return_value = sample_book
        mock_book_service_instance.update_book_tags.return_value = updated_book
        mock_book_service_class.return_value = mock_book_service_instance

        # Создаём мок для Update
        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "   "  # Только пробелы
        update.message.reply_text = AsyncMock()

        # Создаём мок для контекста
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {
            "edit_state": "editing_tags",
            "selected_book_id": "test-book-1"
        }

        # Вызываем обработчик
        await handle_edit_tags_message(update, context)

        # Проверяем, что сообщение было отправлено
        update.message.reply_text.assert_called_once()
        message_text = update.message.reply_text.call_args[0][0]

        # Проверяем, что в сообщении указано об успешном обновлении
        assert "Тэги книги успешно обновлены" in message_text
        assert "Нет тэгов" in message_text
        
        # Проверяем, что BookService был создан
        mock_book_service_class.assert_called_once()
        # Проверяем, что были вызваны нужные методы
        mock_book_service_instance.get_book_by_id.assert_called_once_with("test-book-1")
        mock_book_service_instance.update_book_tags.assert_called_once_with("test-book-1", [])

@pytest.mark.asyncio
async def test_handle_edit_tags_message_wrong_state(book_service):
    """Тест обработчика сообщения при неправильном состоянии."""
    # Создаём мок для Update
    update = MagicMock()
    update.message = MagicMock()
    update.message.text = "новые тэги"
    update.message.reply_text = AsyncMock()

    # Создаём мок для контекста
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {
        "edit_state": "some_other_state"
    }

    # Вызываем обработчик
    await handle_edit_tags_message(update, context)

    # Проверяем, что сообщение не было отправлено (обработчик должен вернуть без действий)
    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_handle_cancel_operation_callback():
    """Тест обработчика callback для отмены операции."""
    from src.bot.keyboards import main as keyboards
    
    # Создаём мок для Update
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.data = "cancel_operation"
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.message = MagicMock()  # Добавляем message к callback_query
    update.callback_query.message.reply_text = AsyncMock()

    # Создаём мок для контекста
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {
        "edit_state": "editing_tags",
        "selected_book_id": "test-book-1"
    }

    # Импортируем обработчик из callbacks
    from src.bot.handlers.callbacks import handle_callback

    # Вызываем обработчик
    await handle_callback(update, context)

    # Проверяем, что состояние очищено
    assert context.user_data == {}

    # Проверяем, что сообщение было отредактировано
    update.callback_query.edit_message_text.assert_called_once_with("Операция отменена")

    # Проверяем, что отправлено сообщение с главным меню
    update.callback_query.message.reply_text.assert_called_once()
    args, kwargs = update.callback_query.message.reply_text.call_args
    assert "Что вы хотите сделать дальше?" in args[0]
    assert isinstance(kwargs['reply_markup'], type(keyboards.main_menu()))
