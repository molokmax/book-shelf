"""Клавиатура для выбора метода добавления книги.""" 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def add_method_selection() -> InlineKeyboardMarkup:
    """Клавиатура для выбора метода добавления книги."""
    keyboard = [
        [
            InlineKeyboardButton("📝 Вручную", callback_data="add_method:manual")
        ],
        [
            InlineKeyboardButton("❌ Отмена", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
