"""Обработчики команды /edit в VK‑боте (только удаление книги)."""

from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id
from vk_api.vk_api import VkApiMethod

from core.services import BookService
from utils import helpers, logger
from utils.helpers import get_status_name
from vk_bot.keyboards import cancel_keyboard, main_keyboard
from vk_bot.states import active_states
from vk_bot.user_helpers import get_or_create_user

log = logger.setup_logger(__name__)

# TODO: Актуализировать DevNotes.md
# TODO: пофиксить flake8 src/
# TODO: код получения книги вынести в отдельный метод
# TODO: сделать отдельный класс для обработчиков команд

def handle_edit_command(vk: VkApiMethod, user_id: int) -> None:
    """Инициирует процесс /edit – выводит нумерованный список книг и просит выбрать номер."""
    # 1. Получаем пользователя
    user = get_or_create_user(vk, user_id)

    # 2. Получаем и сортируем книги
    book_service = BookService()
    books = book_service.get_all_books(user.id)
    books = helpers.sort_books_by_status(books)

    # 3. Если книг нет – отправляем сообщение
    if not books:
        vk.messages.send(
            user_id=user_id,
            message="У тебя нет книг в библиотеке. Добавь книгу с помощью /add",
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        return

    # 4. Формируем нумерованный список в одном сообщении
    lines = ["📚 Введи номер книги, которую хочешь отредактировать.\nТвоя библиотека:\n\n"]
    for i, book in enumerate(books, 1):
        lines.append(helpers.format_book_info(i, book) + "\n")
    message_text = "".join(lines)

    # 5. Сохраняем состояние
    active_states[user_id] = {"command": "/edit", "state": "selecting_book", "data": {"books": [book.id for book in books]}}

    # 6. Отправляем список и запрос номера
    vk.messages.send(
        user_id=user_id,
        message=message_text,
        keyboard=cancel_keyboard().get_keyboard(),
        random_id=get_random_id()
    )


def handle_edit_command_step(vk: VkApiMethod, user_id: int, text: str) -> None:
    """Обрабатывает шаг после выбора книги в режиме /edit."""
    state_info = active_states.get(user_id)
    if not state_info or state_info.get("command") != "/edit":
        return
    
    state = state_info.get("state")

    if state == "selecting_book":
        # Ожидаем номер книги
        try:
            selection = int(text.strip())
        except ValueError:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Введи корректный номер книги.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        books_ids = state_info["data"]["books"]
        if selection < 1 or selection > len(books_ids):
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Номер книги вне диапазона.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        book_id = books_ids[selection - 1]
        book_service = BookService()
        selected_book = book_service.get_book_by_id(book_id)
        if not selected_book:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

        # Сохраняем выбранную книгу и переходим к выбору действия
        state_info["state"] = "selecting_action"
        state_info["data"]["selected_book_id"] = book_id
        # Предлагаем действие (пока только удаление)
        vk.messages.send(
            user_id=user_id,
            message=f"Выбрана книга '{selected_book.title}'. Что нужно сделать?",
            keyboard=create_book_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        return
    
    if state == "selecting_action":
        if text.lower() == "удалить":
            book_service = BookService()
            book_id = state_info["data"]["selected_book_id"]
            if not book_id:
                vk.messages.send(
                    user_id=user_id,
                    message="Ошибка при удалении книги. Идентификатор выбранной книги отсутствует.",
                    keyboard=cancel_keyboard().get_keyboard(),
                    random_id=get_random_id()
                )
                return

            deleted_book = book_service.delete_book(book_id)
            del active_states[user_id]
            vk.messages.send(
                user_id=user_id,
                message=f"🗑️ Книга '{deleted_book.title}' удалена.",
                keyboard=main_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        
        elif text.lower() == "прогресс":
            # Начинаем процесс обновления прогресса чтения
            book_id = state_info["data"]["selected_book_id"]
            book_service = BookService()
            book = book_service.get_book_by_id(book_id)
            if not book:
                vk.messages.send(
                    user_id=user_id,
                    message="⚠️ Книга не найдена.",
                    keyboard=cancel_keyboard().get_keyboard(),
                    random_id=get_random_id()
                )
                return

            # Сохраняем состояние ожидания ввода текущей страницы
            state_info["state"] = "waiting_for_progress_input"
            state_info["data"]["progress_book_pages"] = book.pages
            vk.messages.send(
                user_id=user_id,
                message=(
                    f"📖 Выбрана книга '{book.title}'. Введи текущую страницу (от 0 до {book.pages}):"
                ),
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        
        elif text.lower() == "статус":
            book_id = state_info["data"]["selected_book_id"]
            book_service = BookService()
            book = book_service.get_book_by_id(book_id)
            if not book:
                vk.messages.send(
                    user_id=user_id,
                    message="⚠️ Книга не найдена.",
                    keyboard=cancel_keyboard().get_keyboard(),
                    random_id=get_random_id()
                )
                return

            state_info["state"] = "selecting_status"
            vk.messages.send(
                user_id=user_id,
                message=(
                    f"📖 Выбрана книга '{book.title}'. Выбери новый статус:"
                ),
                keyboard=create_status_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        
        elif text.lower() == "изменить":
            book_id = state_info["data"]["selected_book_id"]
            book_service = BookService()
            book = book_service.get_book_by_id(book_id)
            if not book:
                vk.messages.send(
                    user_id=user_id,
                    message="⚠️ Книга не найдена.",
                    keyboard=cancel_keyboard().get_keyboard(),
                    random_id=get_random_id()
                )
                return

            state_info["state"] = "editing_title"
            vk.messages.send(
                user_id=user_id,
                message=f"Текущее название книги: '{book.title}'. Введи новое название или нажми 'Дальше' чтобы оставить текущего.",
                keyboard=create_edit_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

    elif state == "editing_title":
        # Ожидаем ввод нового названия книги или пропуск
        if text.lower() == "дальше":
            # Оставляем текущее название
            new_title = None
        else:
            new_title = text.strip()
        # Сохраняем в состоянии и переходим к автору
        state_info["data"]["new_title"] = new_title
        state_info["state"] = "editing_author"
        book_id = state_info["data"]["selected_book_id"]
        book = BookService().get_book_by_id(book_id)
        if not book:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
    
        vk.messages.send(
            user_id=user_id,
            message=f"Текущий автор книги: '{book.author}'. Введи нового автора или нажми 'Дальше' чтобы оставить текущего.",
            keyboard=create_edit_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        return
    
    elif state == "editing_author":
        if text.lower() == "дальше":
            new_author = None
        else:
            new_author = text.strip()
        state_info["data"]["new_author"] = new_author
        state_info["state"] = "editing_pages"
        book_id = state_info["data"]["selected_book_id"]
        book = BookService().get_book_by_id(book_id)
        if not book:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        
        vk.messages.send(
            user_id=user_id,
            message=f"Текущее количество страниц: {book.pages}. Введи новое количество страниц или нажми 'Дальше' чтобы оставить текущие.",
            keyboard=create_edit_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        return
    
    elif state == "editing_pages":
        if text.lower() == "дальше":
            new_pages = None
        else:
            try:
                new_pages = int(text.strip())
            except ValueError:
                vk.messages.send(
                    user_id=user_id,
                    message="⚠️ Введите корректное целое число для количества страниц.",
                    keyboard=create_edit_keyboard().get_keyboard(),
                    random_id=get_random_id()
                )
                return
        
        state_info["data"]["new_pages"] = new_pages
        state_info["state"] = "editing_link"
        book_id = state_info["data"]["selected_book_id"]
        book = BookService().get_book_by_id(book_id)
        if not book:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        
        vk.messages.send(
            user_id=user_id,
            message=f"Текущая ссылка на книгу - {book.link or 'Отсутствует'}. Введи новую ссылку на книгу или нажми 'Дальше' чтобы оставить текущую.",
            keyboard=create_edit_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        return
    
    elif state == "editing_link":
        if text.lower() == "дальше":
            new_link = None
        else:
            new_link = text.strip()
        state_info["data"]["new_link"] = new_link
        state_info["state"] = "editing_tags"
        book_id = state_info["data"]["selected_book_id"]
        book = BookService().get_book_by_id(book_id)
        if not book:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        
        tags_text = ", ".join(book.tags) if book.tags else "Нет тэгов"
        vk.messages.send(
            user_id=user_id,
            message=f"Текущие тэги книги: {tags_text}. Введи новые тэги через запятую или нажми 'Дальше' чтобы оставить текущие.",
            keyboard=create_edit_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        return
    
    elif state == "editing_tags":
        if text.lower() == "дальше":
            new_tags = None
        else:
            new_tags = [t.strip() for t in text.split(',') if t.strip()]
        # Применяем изменения
        book_id = state_info["data"]["selected_book_id"]
        book_service = BookService()
        book = book_service.get_book_by_id(book_id)
        if not book:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Книга не найдена.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        
        if state_info["data"]["new_title"] is not None:
            book.title = state_info["data"]["new_title"]
        if state_info["data"]["new_author"] is not None:
            book.author = state_info["data"]["new_author"]
        if state_info["data"]["new_pages"] is not None:
            book.pages = state_info["data"]["new_pages"]
        if state_info["data"]["new_link"] is not None:
            book.link = state_info["data"]["new_link"]
        if new_tags is not None:
            book.tags = new_tags
        book_service.book_repo.update_book(book)
        vk.messages.send(
            user_id=user_id,
            message=f"✅ Книга обновлена: '{book.title}' от {book.author}.",
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        del active_states[user_id]
        return
    
    elif state == "waiting_for_progress_input":
        # Обработка ввода текущей страницы пользователем
        try:
            current_page = int(text.strip())
        except ValueError:
            vk.messages.send(
                user_id=user_id,
                message="❌ Некорректный ввод. Пожалуйста, введи число (например: '50').",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

        total_pages = state_info["data"].get("progress_book_pages")
        if total_pages is None:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Ошибка: неизвестное количество страниц книги.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

        if current_page < 0:
            vk.messages.send(
                user_id=user_id,
                message="❌ Страница не может быть отрицательной.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return
        if current_page > total_pages:
            vk.messages.send(
                user_id=user_id,
                message=f"❌ Книга содержит только {total_pages} страниц.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

        book_id = state_info["data"].get("selected_book_id")
        if not book_id:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Идентификатор книги не найден.",
                keyboard=cancel_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

        book_service = BookService()
        updated_book = book_service.update_book_progress(book_id, current_page)

        vk.messages.send(
            user_id=user_id,
            message=(
                f"✅ Прогресс чтения книги '{updated_book.title}' обновлён.\n"
                f"Прочитано {updated_book.current_page} из {total_pages} страниц."
            ),
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        # Очистить состояние
        del active_states[user_id]
        return

    elif state == "selecting_status":
        # Обрабатываем выбор нового статуса книги
        status_map = {
            "хочу прочитать": "want_to_read",
            "читаю сейчас": "reading",
            "прочитано": "read",
            "отложено": "postponed",
        }
        new_status = status_map.get(text.lower())
        if not new_status:
            vk.messages.send(
                user_id=user_id,
                message="⚠️ Неизвестный статус. Выбери один из предложенных.",
                keyboard=create_status_keyboard().get_keyboard(),
                random_id=get_random_id()
            )
            return

        book_id = state_info["data"]["selected_book_id"]
        book_service = BookService()
        updated_book = book_service.update_book_status(book_id, new_status)

        vk.messages.send(
            user_id=user_id,
            message=f"✅ Статус книги '{updated_book.title}' изменён на '{get_status_name(updated_book.status.value)}'",
            keyboard=main_keyboard().get_keyboard(),
            random_id=get_random_id()
        )
        del active_states[user_id]
        return


def create_book_keyboard() -> VkKeyboard:
    """Создаёт клавиатуру с кнопками действий над книгой: удалить, прогресс, статус и изменить."""
    kb = VkKeyboard()
    kb.add_button('Изменить')
    kb.add_button('Прогресс')
    kb.add_button('Статус')
    kb.add_line()
    kb.add_button('Удалить')
    kb.add_button('Отмена', payload={'command': '/cancel'})
    return kb


def create_status_keyboard() -> VkKeyboard:
    """Создаёт клавиатуру для выбора нового статуса книги без payload."""
    kb = VkKeyboard()
    # Кнопки с названием статуса, без payload; обработка будет по тексту сообщения
    kb.add_button('Хочу прочитать')
    kb.add_button('Читаю сейчас')
    kb.add_line()
    kb.add_button('Прочитано')
    kb.add_button('Отложено')
    kb.add_line()
    kb.add_button('Отмена', payload={'command': '/cancel'})
    return kb


def create_edit_keyboard() -> VkKeyboard:
    """Keyboard with 'Дальше' and 'Отмена' buttons for sequential editing steps."""
    kb = VkKeyboard()
    kb.add_button('Дальше')
    kb.add_button('Отмена', payload={'command': '/cancel'})
    return kb