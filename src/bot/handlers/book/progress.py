"""Обработчики команды /progress и связанных с ней сообщений и callback-ов."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import helpers, logger
from core.services import BookService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def update_progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /progress."""
    user = helpers.get_or_create_user(update)

    book_service = BookService()
    books = book_service.get_all_books(user.id)

    if not books:
        await update.message.reply_text("Ваша библиотека пуста. Добавьте первую книгу с помощью /add")
        return

    # Показываем список книг с их текущим прогрессом
    response = "📚 Выберите книгу для обновления прогресса:\n\n"
    for i, book in enumerate(books, 1):
        status_emoji = {
            "want_to_read": "📖",
            "reading": "📚",
            "read": "📕",
            "postponed": "⏸️"
        }.get(book.status, "📘")

        response += f"{i}. {status_emoji} **{book.title}** - Страница {book.progress}/{book.pages}\n"

    response += "\nПожалуйста, отправьте номер книги и текущую страницу (например: '1 50' для страницы 50):"
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=keyboards.cancel_keyboard())

    # Сохраняем состояние для следующих шагов
    context.user_data["state"] = "waiting_for_progress_update"
    context.user_data["user_id"] = user.id

async def handle_progress_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик обновления прогресса чтения."""
    try:
        user_id = context.user_data["user_id"]
        text = update.message.text.strip()

        # Парсим номер книги и страницу
        parts = text.split()
        if len(parts) != 2:
            raise ValueError("Некорректный формат")

        book_index = int(parts[0]) - 1  # Преобразуем в индекс (0-based)
        current_page = int(parts[1])

        book_service = BookService()
        books = book_service.get_all_books(user_id)

        if book_index < 0 or book_index >= len(books):
            raise ValueError("Некорректный номер книги")

        book = books[book_index]

        if current_page < 0:
            raise ValueError("Страница не может быть отрицательной")

        if current_page > book.pages:
            await update.message.reply_text(
                f"⚠️ Предупреждение: Вы указали страницу {current_page}, но в книге всего {book.pages} страниц.\n"
                "Прогресс будет установлен в 100%. Продолжить?",
                reply_markup=keyboards.confirm_keyboard("update_progress_confirm")
            )
            # Сохраняем данные для подтверждения
            context.user_data["progress_update_book_id"] = book.id
            context.user_data["progress_update_page"] = current_page
            context.user_data["state"] = "waiting_for_progress_confirm"
            return

        # Рассчитываем прогресс в процентах
        progress_percent = min(100, round((current_page / book.pages) * 100))

        # Обновляем прогресс
        updated_book = book_service.update_book_progress(book.id, progress_percent)

        # Очищаем состояние
        context.user_data.clear()

        await update.message.reply_text(
            f"✅ Прогресс книги '{updated_book.title}' обновлён!\n"
            f"Текущая страница: {current_page}/{updated_book.pages} ({progress_percent}%)",
            reply_markup=keyboards.main_menu()
        )

    except ValueError as e:
        await update.message.reply_text(
            f"❌ Некорректный ввод. Пожалуйста, отправьте номер книги и текущую страницу (например: '1 50').\n"
            f"Ошибка: {str(e)}",
            reply_markup=keyboards.cancel_keyboard()
        )

async def handle_progress_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик подтверждения обновления прогресса."""
    text = update.message.text.strip().lower()
    if text in ["да", "yes", "д", "y"]:
        book_service = BookService()
        book_id = context.user_data["progress_update_book_id"]
        current_page = context.user_data["progress_update_page"]

        book = book_service.get_book_by_id(book_id)
        if book:
            progress_percent = 100
            updated_book = book_service.update_book_progress(book_id, progress_percent)

            # Очищаем состояние
            context.user_data.clear()

            await update.message.reply_text(
                f"✅ Прогресс книги '{updated_book.title}' обновлён!\n"
                f"Текущая страница: {current_page}/{updated_book.pages} (100%)",
                reply_markup=keyboards.main_menu()
            )
        else:
            await update.message.reply_text(
                "❌ Книга не найдена.",
                reply_markup=keyboards.main_menu()
            )
    else:
        # Отмена обновления
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Обновление прогресса отменено.",
            reply_markup=keyboards.main_menu()
        )

async def handle_progress_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback для быстрого обновления прогресса."""
    query = update.callback_query

    data = query.data.split(":")
    if data[0] == "update_progress":
        try:
            book_id = int(data[1])
            new_progress = int(data[2])

            book_service = BookService()
            book = book_service.update_book_progress(book_id, new_progress)

            await query.edit_message_text(
                f"✅ Прогресс чтения книги '{book.title}' обновлён до {book.progress}%",
                reply_markup=keyboards.main_menu()
            )
        except Exception as e:
            log.error(f"Ошибка при обновлении прогресса: {e}")
            await query.edit_message_text("❌ Произошла ошибка при обновлении прогресса")
