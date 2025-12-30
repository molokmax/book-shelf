"""Обработчики текстовых сообщений для Telegram-бота."""
\
from telegram import Update
from telegram.ext import ContextTypes

from utils import logger
from core.services import BookService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    text = update.message.text.strip()

    # Проверяем, есть ли активный диалог добавления книги
    state = context.user_data.get("state")
    if state == "waiting_for_title":
        # Сохраняем название книги
        context.user_data["book_title"] = text
        await update.message.reply_text(
            "Отлично! Теперь введите автора книги:",
            reply_markup=keyboards.cancel_keyboard()
        )
        context.user_data["state"] = "waiting_for_author"
        return

    if state == "waiting_for_author":
        # Сохраняем автора
        context.user_data["book_author"] = text
        await update.message.reply_text(
            "Хорошо! Теперь введите теги книги через запятую (например: Tech, Программирование):",
            reply_markup=keyboards.cancel_keyboard()
        )
        context.user_data["state"] = "waiting_for_tags"
        return

    if state == "waiting_for_tags":
        # Сохраняем теги
        context.user_data["book_tags"] = [tag.strip() for tag in text.split(",") if tag.strip()]
        await update.message.reply_text(
            "Отлично! Теперь введите количество страниц в книге:",
            reply_markup=keyboards.cancel_keyboard()
        )
        context.user_data["state"] = "waiting_for_pages"
        return

    if state == "waiting_for_pages":
        # Сохраняем количество страниц и создаём книгу
        try:
            pages = int(text)
            if pages <= 0:
                raise ValueError

            book_service = BookService()
            book = book_service.create_book(
                title=context.user_data["book_title"],
                author=context.user_data["book_author"],
                tags=context.user_data["book_tags"],
                pages=pages
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

        except ValueError:
            await update.message.reply_text(
                "❌ Некорректное количество страниц. Пожалуйста, введите число.",
                reply_markup=keyboards.cancel_keyboard()
            )
        return

    if state == "waiting_for_progress_update":
        # Обрабатываем обновление прогресса чтения
        try:
            # Парсим номер книги и страницу
            parts = text.split()
            if len(parts) != 2:
                raise ValueError("Некорректный формат")

            book_index = int(parts[0]) - 1  # Преобразуем в индекс (0-based)
            current_page = int(parts[1])

            book_service = BookService()
            books = book_service.get_all_books()

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
        return

    if state == "waiting_for_progress_confirm":
        # Обрабатываем подтверждение обновления прогресса
        if text.lower() in ["да", "yes", "д", "y"]:
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
        return

    # Если нет активного диалога, показываем помощь
    await update.message.reply_text(
        "Я не понял ваше сообщение. Используйте команды:\n\n"
        "/start - Начало работы\n"
        "/help - Помощь\n"
        "/add - Добавить книгу\n"
        "/list - Показать список книг",
        reply_markup=keyboards.main_menu()
    )
