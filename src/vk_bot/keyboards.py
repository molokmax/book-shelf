from vk_api.keyboard import VkKeyboard

from core.models import ReadingStatus
from utils.helpers import get_status_name


def main_keyboard() -> VkKeyboard:
    """Главная клавиатура бота."""
    kb = VkKeyboard()
    kb.add_button("/list")
    kb.add_button("/edit")
    kb.add_button("/add")
    kb.add_button("/details")
    kb.add_line()
    kb.add_button("/stats")
    kb.add_button("/export")
    kb.add_button("/help")
    return kb


def cancel_keyboard() -> VkKeyboard:
    """Клавиатура отмены операции."""
    kb = VkKeyboard()
    kb.add_button("Отмена", payload={"command": "/cancel"})
    return kb


def filter_keyboard() -> VkKeyboard:
    """Клавиатура выбора фильтра для списка книг."""
    kb = VkKeyboard()
    kb.add_button("По статусу")
    kb.add_button("По тегам")
    kb.add_line()
    kb.add_button("Все")
    kb.add_button("Отмена", payload={"command": "/cancel"})
    return kb


def status_keyboard() -> VkKeyboard:
    """Клавиатура выбора статуса книги."""
    kb = VkKeyboard()
    for i, status in enumerate(ReadingStatus, 1):
        status_name = get_status_name(status)
        kb.add_button(status_name, payload={"status": status.value})
        if i % 2 == 0:
            kb.add_line()
    kb.add_button("Отмена", payload={"command": "/cancel"})
    return kb


def tags_keyboard(available_tags: list[str]) -> VkKeyboard:
    """Клавиатура выбора тега(ов) из доступных тегов."""
    kb = VkKeyboard()
    for i, tag in enumerate(available_tags, 1):
        kb.add_button(tag)
        if i % 2 == 0:
            kb.add_line()
    kb.add_button("Отмена", payload={"command": "/cancel"})
    return kb
