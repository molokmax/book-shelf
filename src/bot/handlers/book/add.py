"""Обработчики команды /add и связанных с ней сообщений и callback-ов."""

from telegram import Update
from telegram.ext import ContextTypes

from bot import tg_helpers
from utils import logger
from utils.litres_parser import parse_litres_book, is_litres_url, LitresParserError
from core.services import BookService
from bot.keyboards import main as keyboards
from bot.keyboards.add_method import add_method_selection

log = logger.setup_logger(__name__)

async def add_book_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /add."""
    user = tg_helpers.get_or_create_user(update)

    await update.message.reply_text(
        "📖 Добавление новой книги\n\n"
        "Пожалуйста, выберите способ добавления книги:",
        reply_markup=add_method_selection()
    )
    # Сохраняем состояние для выбора метода
    context.user_data["state"] = "selecting_add_method"
    context.user_data["user_id"] = user.id

async def handle_add_book_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик названия книги."""
    # Сохраняем название книги
    context.user_data["book_title"] = update.message.text.strip()
    await update.message.reply_text(
        "Отлично! Теперь введите автора книги:",
        reply_markup=keyboards.cancel_keyboard()
    )
    context.user_data["state"] = "waiting_for_author"

async def handle_add_book_author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик автора книги."""
    # Сохраняем автора
    context.user_data["book_author"] = update.message.text.strip()
    await update.message.reply_text(
        "Хорошо! Теперь введите теги книги через запятую (например: Tech, Программирование):",
        reply_markup=keyboards.cancel_keyboard()
    )
    context.user_data["state"] = "waiting_for_tags"

async def handle_add_book_tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик тегов книги."""
    # Сохраняем теги
    context.user_data["book_tags"] = [tag.strip() for tag in update.message.text.split(",") if tag.strip()]
    await update.message.reply_text(
        "Отлично! Теперь введите количество страниц в книге:",
        reply_markup=keyboards.cancel_keyboard()
    )
    context.user_data["state"] = "waiting_for_pages"

async def handle_add_book_pages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик количества страниц."""
    # Сохраняем количество страниц и запрашиваем приоритет
    pages = int(update.message.text.strip())
    if pages <= 0:
        raise ValueError

    user_id = context.user_data["user_id"]

    book_service = BookService()
    book = book_service.create_book(
        title=context.user_data["book_title"],
        author=context.user_data["book_author"],
        tags=context.user_data["book_tags"],
        pages=pages,
        user_id=user_id
    )

    # Очищаем состояние
    context.user_data.clear()

    await update.message.reply_text(
        f"✅ Книга '{book.title}' успешно добавлена в вашу библиотеку!\n\n"
        "Вы можете:\n"
        "/list - Посмотреть все книги\n"
        "/add - Добавить ещё одну книгу",
        reply_markup=keyboards.main_menu()
    )

async def handle_add_book_from_litres(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ссылки на книгу из Литрес."""
    # Получаем URL из сообщения
    litres_url = update.message.text.strip()

    try:
        # Парсим информацию о книге с Литрес
        book_data = parse_litres_book(litres_url)

        # Проверяем обязательные параметры
        if not book_data.get('title') or not book_data.get('author') or book_data.get('pages') <= 0:
            raise LitresParserError("Не удалось получить обязательные параметры книги")

        # Сохраняем данные книги
        context.user_data["book_title"] = book_data['title']
        context.user_data["book_author"] = book_data['author']
        context.user_data["book_pages"] = book_data['pages']
        context.user_data["book_cover"] = book_data.get('cover_image')

        # Показываем пользователю полученные данные для подтверждения
        message = (
            f"📖 Нашли книгу на Литрес!\n\n"
            f"Название: {book_data['title']}\n"
            f"Автор: {book_data['author']}\n"
            f"Страниц: {book_data['pages']}\n"
        )

        if book_data.get('cover_image'):
            message += f"Обложка: {book_data['cover_image']}\n"

        message += "\n\n✅ Подтвердите добавление книги?"

        await update.message.reply_text(
            message,
            reply_markup=keyboards.confirm_add_keyboard()
        )
        context.user_data["state"] = "confirming_litres_book"

    except LitresParserError as e:
        await update.message.reply_text(
            f"❌ Ошибка при получении информации о книге:\n{str(e)}\n\n"
            "Пожалуйста, проверьте ссылку и попробуйте ещё раз.",
            reply_markup=keyboards.cancel_keyboard()
        )
        context.user_data["state"] = "waiting_for_litres_url"
    except Exception as e:
        log.error(f"Неожиданная ошибка при добавлении книги из Литрес: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при добавлении книги. Пожалуйста, попробуйте позже.",
            reply_markup=keyboards.cancel_keyboard()
        )
        context.user_data["state"] = "waiting_for_litres_url"

async def handle_confirm_litres_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик подтверждения добавления книги из Литрес."""
    query = update.callback_query
    data = query.data.split(":")

    if len(data) < 2:
        return

    action = data[1]

    if action == "confirm":
        # Запрашиваем теги у пользователя
        await query.edit_message_text(
            "Отлично! Теперь введите теги книги через запятую (например: Tech, Программирование):"
        )
        context.user_data["state"] = "waiting_for_litres_tags"
    elif action == "cancel":
        # Отмена добавления
        context.user_data.clear()
        await query.edit_message_text(
            "❌ Добавление книги отменено.",
            reply_markup=keyboards.main_menu()
        )

async def handle_litres_book_tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик тегов книги из Литрес."""
    # Сохраняем теги
    context.user_data["book_tags"] = [tag.strip() for tag in update.message.text.split(",") if tag.strip()]

    # Создаём книгу
    user_id = context.user_data["user_id"]
    book_service = BookService()

    book = book_service.create_book(
        title=context.user_data["book_title"],
        author=context.user_data["book_author"],
        tags=context.user_data["book_tags"],
        pages=context.user_data["book_pages"],
        user_id=user_id
    )

    # Очищаем состояние
    context.user_data.clear()

    await update.message.reply_text(
        f"✅ Книга '{book.title}' успешно добавлена в вашу библиотеку!\n\n"
        "Вы можете:\n"
        "/list - Посмотреть все книги\n"
        "/add - Добавить ещё одну книгу",
        reply_markup=keyboards.main_menu()
    )

async def handle_add_method_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора метода добавления книги."""
    query = update.callback_query
    data = query.data.split(":")

    if len(data) < 2:
        return

    method = data[1]

    if method == "manual":
        # Ручное добавление книги
        await query.edit_message_text(
            "📖 Добавление новой книги"
        )
        await query.message.reply_text(
            "Пожалуйста, введите название книги:",
            reply_markup=keyboards.cancel_keyboard()
        )
        # Сохраняем состояние для следующих шагов
        context.user_data["state"] = "waiting_for_title"
    elif method == "litres":
        # Добавление книги из Литрес
        await query.edit_message_text(
            "🔗 Добавление книги из Литрес"
        )
        await query.message.reply_text(
            "Пожалуйста, введите ссылку на книгу с Литрес:",
            reply_markup=keyboards.cancel_keyboard()
        )
        # Сохраняем состояние для следующих шагов
        context.user_data["state"] = "waiting_for_litres_url"
