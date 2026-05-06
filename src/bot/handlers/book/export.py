"""Обработчики команды /export и связанных с ней сообщений и callback-ов."""

import csv
import io
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from bot import tg_helpers
from utils import logger
from core.services import BookService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /export."""
    user = tg_helpers.get_or_create_user(update)

    book_service = BookService()
    books = book_service.get_all_books(user.id)

    if not books:
        await update.message.reply_text(
            "📚 У вас нет книг в библиотеке для экспорта.",
            reply_markup=keyboards.main_menu()
        )
        return

    # Создаём CSV файл в памяти
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Записываем заголовки
    writer.writerow([
        "ID",
        "Название",
        "Автор",
        "Теги",
        "Общее количество страниц",
        "Текущая страница",
        "Статус",
        "Дата создания",
        "Дата обновления",
        "Обложка",
        "Заметки",
        "Дата начала чтения",
        "Дата окончания чтения"
    ])

    # Записываем книги
    for book in books:
        writer.writerow([
            book.id,
            book.title,
            book.author,
            ", ".join(book.tags) if book.tags else "",
            book.pages,
            book.current_page,
            book.status.value,
            book.created_at.strftime("%d.%m.%Y %H:%M"),
            book.updated_at.strftime("%d.%m.%Y %H:%M"),
            book.cover_image if book.cover_image else "",
            book.notes if book.notes else "",
            book.reading_start_date.strftime("%d.%m.%Y %H:%M") if book.reading_start_date else "",
            book.reading_end_date.strftime("%d.%m.%Y %H:%M") if book.reading_end_date else ""
        ])

    # Формируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"books_export_{timestamp}.csv"

    # Отправляем файл пользователю
    await update.message.reply_text(
        "📥 Экспорт библиотеки завершён!\n\n"
        "Файл с вашими книгами отправлен ниже.",
        reply_markup=keyboards.main_menu()
    )

    # Отправляем CSV файл
    csv_content = output.getvalue()
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=csv_content.encode('utf-8'),
        filename=filename,
        caption=f"Экспорт библиотеки ({len(books)} книг)"
    )
