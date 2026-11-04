import math

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from core.models import ReadingStatus
from utils.helpers import get_status_name

TAGS_PER_PAGE = 16  # 8 рядов по 2 кнопки, чтобы вместить «Готово», «Отмена» и пагинацию
TAGS_PER_ROW = 2


def main_keyboard() -> VkKeyboard:
    """Главная клавиатура бота."""
    kb = VkKeyboard()
    kb.add_button("/progress")
    kb.add_button("/details")
    kb.add_button("/list")
    kb.add_line()
    kb.add_button("/add")
    kb.add_button("/help")
    kb.add_button("Ещё", payload={"command": "/more"})
    return kb


def more_keyboard() -> VkKeyboard:
    """Клавиатура подменю «Ещё»."""
    kb = VkKeyboard()
    kb.add_button("/edit")
    kb.add_button("/export")
    kb.add_button("/goal")
    kb.add_line()
    kb.add_button("/stats")
    kb.add_button("/settings")
    kb.add_button("Назад", payload={"command": "/back"})
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


def tag_total_pages(count: int) -> int:
    """Число страниц клавиатуры тегов для набора из count тегов."""
    return max(1, math.ceil(count / TAGS_PER_PAGE))


def tag_editing_keyboard(
    available_tags: list[str],
    selected: list[str],
    page: int,
    owner_command: str,
) -> VkKeyboard:
    """Клавиатура шага выбора тегов книги.

    Теги-переключатели: выбранные подсвечены кнопкой primary. Все кнопки несут
    payload с командой владельца сценария, чтобы маршрутизация не зависела
    от текста кнопки (имя тега может совпадать с командой).
    """
    kb = VkKeyboard()

    ordered = sorted({tag.casefold(): tag for tag in available_tags}.values(), key=str.casefold)
    total_pages = tag_total_pages(len(ordered))
    page = min(max(page, 0), total_pages - 1)
    page_tags = ordered[page * TAGS_PER_PAGE : (page + 1) * TAGS_PER_PAGE]
    selected_keys = {tag.casefold() for tag in selected}

    for index, tag in enumerate(page_tags):
        if index and index % TAGS_PER_ROW == 0:
            kb.add_line()
        color = (
            VkKeyboardColor.PRIMARY
            if tag.casefold() in selected_keys
            else VkKeyboardColor.SECONDARY
        )
        kb.add_button(
            tag,
            color=color,
            payload={"command": owner_command, "action": "toggle", "tag": tag},
        )
    if page_tags:
        kb.add_line()

    kb.add_button(
        "Готово",
        color=VkKeyboardColor.POSITIVE,
        payload={"command": owner_command, "action": "done"},
    )
    kb.add_button("Отмена", color=VkKeyboardColor.NEGATIVE, payload={"command": "/cancel"})

    if total_pages > 1:
        kb.add_line()
        if page > 0:
            kb.add_button("← Назад", payload={"command": owner_command, "action": "prev_page"})
        if page < total_pages - 1:
            kb.add_button("Ещё →", payload={"command": owner_command, "action": "next_page"})

    return kb
