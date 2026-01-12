"""Основные клавиатуры для Telegram-бота."""

from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню с кнопками."""
    keyboard = [
        [
            InlineKeyboardButton("/add 📖"),
            InlineKeyboardButton("/list 📚"),
            InlineKeyboardButton("/progress 📈")
        ],
        [
            InlineKeyboardButton("/priority 🎯"),
            InlineKeyboardButton("/stats 📊"),
            InlineKeyboardButton("/help ❓")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""
    keyboard = [
        ["/cancel ❌"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def status_keyboard(book_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для изменения статуса книги."""
    keyboard = [
        [
            InlineKeyboardButton("📖 Хочу прочитать", callback_data=f"change_status:{book_id}:want_to_read"),
            InlineKeyboardButton("📚 Читаю сейчас", callback_data=f"change_status:{book_id}:reading")
        ],
        [
            InlineKeyboardButton("📕 Прочитано", callback_data=f"change_status:{book_id}:read"),
            InlineKeyboardButton("⏸️ Отложено", callback_data=f"change_status:{book_id}:postponed")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def priority_keyboard(book_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для изменения приоритета книги."""
    keyboard = [
        [
            InlineKeyboardButton("🔴 Высокий", callback_data=f"change_priority:{book_id}:high"),
            InlineKeyboardButton("🟡 Средний", callback_data=f"change_priority:{book_id}:medium"),
        # ],
        # [
            InlineKeyboardButton("🟢 Низкий", callback_data=f"change_priority:{book_id}:low")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def book_actions_keyboard(book_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для действий с книгой."""
    keyboard = [
        [
            InlineKeyboardButton("📋 Изменить статус", callback_data=f"change_status:{book_id}:want_to_read"),
            InlineKeyboardButton("🎯 Изменить приоритет", callback_data=f"change_priority:{book_id}:high")
        ],
        [
            InlineKeyboardButton("📊 Обновить прогресс", callback_data=f"update_progress:{book_id}:0"),
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_book:{book_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(callback_data: str) -> ReplyKeyboardMarkup:
    """Клавиатура с кнопками подтверждения/отмены."""
    keyboard = [
        [
            "/yes ✅",
            "/no ❌"
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
