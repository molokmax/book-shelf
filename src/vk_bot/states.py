"""Имена шагов сценариев и общих под-сценариев.

Значения совпадают со строками, которые уже сохранены в ``user_state``,
поэтому переход на перечисления не требует миграции данных.
"""

from enum import StrEnum


class SelectionState(StrEnum):
    """Общие шаги выбора книги (BookSelectionFlow и его потребители)."""

    CHOOSE_FILTER = "choose_filter"
    SELECTING_STATUS_FILTER = "selecting_status_filter"
    SELECTING_TAG_FILTER = "selecting_tag_filter"
    SELECTING_BOOK = "selecting_book"


class TagState(StrEnum):
    """Общий шаг выбора тегов (TagEditingFlow)."""

    SELECTING_TAGS = "selecting_tags"


class ProgressState(StrEnum):
    """Общие шаги обновления прогресса (ProgressUpdateFlow)."""

    WAITING_FOR_PROGRESS_INPUT = "waiting_for_progress_input"
    WAITING_FOR_PROGRESS_CONFIRM = "waiting_for_progress_confirm"


class AddState(StrEnum):
    """Шаги сценария /add."""

    CHOOSE_METHOD = "choose_method"
    WAITING_FOR_TITLE = "waiting_for_title"
    WAITING_FOR_AUTHOR = "waiting_for_author"
    WAITING_FOR_PAGES = "waiting_for_pages"
    WAITING_FOR_LINK = "waiting_for_link"
    SELECTING_TAGS = "selecting_tags"
    WAITING_FOR_LITRES_URL = "waiting_for_litres_url"
    WAITING_FOR_LITRES_CONFIRM = "waiting_for_litres_confirm"


class EditState(StrEnum):
    """Шаги сценария /edit."""

    CHOOSE_FILTER = "choose_filter"
    SELECTING_STATUS_FILTER = "selecting_status_filter"
    SELECTING_TAG_FILTER = "selecting_tag_filter"
    SELECTING_BOOK = "selecting_book"
    SELECTING_ACTION = "selecting_action"
    EDITING_TITLE = "editing_title"
    EDITING_AUTHOR = "editing_author"
    EDITING_PAGES = "editing_pages"
    EDITING_LINK = "editing_link"
    SELECTING_TAGS = "selecting_tags"
    SELECTING_STATUS = "selecting_status"


class DetailsState(StrEnum):
    """Шаги сценария /details."""

    CHOOSE_FILTER = "choose_filter"
    SELECTING_STATUS_FILTER = "selecting_status_filter"
    SELECTING_TAG_FILTER = "selecting_tag_filter"
    SELECTING_BOOK = "selecting_book"


class ListState(StrEnum):
    """Шаги сценария /list."""

    CHOOSE_FILTER = "choose_filter"
    CHOOSE_STATUS = "choose_status"
    CHOOSE_TAG = "choose_tag"


class ProgressScenarioState(StrEnum):
    """Шаги сценария /progress (включая шаги общих под-сценариев)."""

    SELECTING_READING_BOOK = "selecting_reading_book"
    CHOOSE_FILTER = "choose_filter"
    SELECTING_STATUS_FILTER = "selecting_status_filter"
    SELECTING_TAG_FILTER = "selecting_tag_filter"
    SELECTING_BOOK = "selecting_book"
    WAITING_FOR_PROGRESS_INPUT = "waiting_for_progress_input"
    WAITING_FOR_PROGRESS_CONFIRM = "waiting_for_progress_confirm"


class GoalState(StrEnum):
    """Шаги сценария /goal."""

    MENU = "menu"
    WAITING_FOR_GOAL_INPUT = "waiting_for_goal_input"


class SettingsState(StrEnum):
    """Шаги сценария /settings."""

    MENU = "menu"
