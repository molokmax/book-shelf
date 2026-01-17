"""Обработчики команды /progress и связанных с ней сообщений и callback-ов."""

from telegram import Update
from telegram.ext import ContextTypes

from utils import helpers, logger
from core.services import BookService
from bot.keyboards import main as keyboards

log = logger.setup_logger(__name__)

async def handle_progress_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback для обновления прогресса чтения."""
    query = update.callback_query

    data = query.data.split(":")
    if data[0] == "update_progress":
        try:
            book_id = data[1]

            # Получаем книгу, чтобы показать её название
            book_service = BookService()
            book = book_service.get_book_by_id(book_id)

            # Просим пользователя ввести текущую страницу
            await query.edit_message_text(
                f"📖 Вы выбрали книгу: **{book.title}**",
                parse_mode="Markdown"
            )
            await query.message.reply_text(
                f"Пожалуйста, введите текущую страницу, на которой вы находитесь (например: '50'):",
                parse_mode="Markdown",
                reply_markup=keyboards.cancel_keyboard()
            )

            # Сохраняем состояние для следующих шагов
            context.user_data["state"] = "waiting_for_progress_input"
            context.user_data["progress_book_id"] = book_id
            context.user_data["progress_book_pages"] = book.pages

        except Exception as e:
            log.error(f"Ошибка при обновлении прогресса: {e}")
            await query.edit_message_text("❌ Произошла ошибка при обновлении прогресса")

async def handle_progress_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода текущей страницы для обновления прогресса."""
    try:
        current_page = int(update.message.text.strip())
        book_id = context.user_data["progress_book_id"]
        total_pages = context.user_data["progress_book_pages"]

        # Проверяем, что страница в пределах допустимого диапазона
        if current_page < 0:
            await update.message.reply_text(
                "❌ Некорректный ввод. Страница не может быть отрицательной.\n"
                "Пожалуйста, введите корректную страницу:",
                reply_markup=keyboards.cancel_keyboard()
            )
            return

        if current_page > total_pages:
            await update.message.reply_text(
                f"❌ Некорректный ввод. Книга содержит только {total_pages} страниц.\n"
                "Пожалуйста, введите корректную страницу:",
                reply_markup=keyboards.cancel_keyboard()
            )
            return

        # Обновляем прогресс в базе (теперь сохраняем текущую страницу)
        book_service = BookService()
        book = book_service.update_book_progress(book_id, current_page)

        # Сообщаем об успешном обновлении
        await update.message.reply_text(
            f"✅ Прогресс чтения книги '{book.title}' обновлён\n"
            f"Вы прочитали {book.current_page} из {total_pages} страниц",
            reply_markup=keyboards.main_menu()
        )

        # Очищаем состояние
        context.user_data.clear()

    except ValueError:
        await update.message.reply_text(
            "❌ Некорректный ввод. Пожалуйста, введите число (например: '50').",
            reply_markup=keyboards.cancel_keyboard()
        )
    except Exception as e:
        log.error(f"Ошибка при обновлении прогресса: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обновлении прогресса",
            reply_markup=keyboards.main_menu()
        )
        context.user_data.clear()
