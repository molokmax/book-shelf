"""Переиспользуемый диалог выбора тегов книги.

Кнопки-переключатели тегов справочника пользователя поверх ввода новых
тегов через запятую. Шаг не завершается, пока пользователь не подтвердит
выборку кнопкой «Готово».
"""

from typing import Callable

from vk_api.utils import get_random_id

from core.services import TagService
from utils import helpers
from vk_bot.context import BotContext
from vk_bot.keyboards import tag_editing_keyboard, tag_total_pages
from vk_bot.user_helpers import get_or_create_user

DONE_TEXT = "готово"


class TagEditingFlow:
    """Диалог выбора тегов книги.

    Компонент не знает, что делать с выборкой: решение принимает колбэк
    ``on_done(context, tags)``, который получает подтверждённую выборку,
    отсортированную по алфавиту.
    """

    def __init__(self, owner_command: str, on_done: Callable[[BotContext, list], None]) -> None:
        self._owner_command = owner_command
        self._on_done = on_done

    def start(
        self,
        context: BotContext,
        state_info: dict,
        preselected: list | None = None,
    ) -> None:
        """Открывает шаг выбора тегов внутри сценария владельца."""
        data = state_info.setdefault("data", {})
        data["selected_tags"] = sorted(preselected or [], key=str.casefold)
        data["tag_page"] = 0
        self._get_user_id(context, state_info)
        state_info["state"] = "selecting_tags"
        context.set_state(state_info)
        self._render(context, state_info)

    def handle(self, context: BotContext) -> None:
        """Обрабатывает действия пользователя на шаге выбора тегов."""
        state_info = context.get_state()
        if state_info.get("state") != "selecting_tags":
            return

        action = context.payload.get("action")
        if action == "toggle":
            self._handle_toggle(context, state_info, context.payload)
        elif action == "done":
            self._handle_done(context, state_info)
        elif action in ("prev_page", "next_page"):
            self._handle_page(context, state_info, action)
        elif (context.text or "").strip().casefold() == DONE_TEXT:
            self._handle_done(context, state_info)
        else:
            self._handle_text(context, state_info)

    # ── Действия на шаге ────────────────────────────────────────────

    def _handle_toggle(self, context: BotContext, state_info: dict, payload: dict) -> None:
        tag = payload.get("tag")
        user_id = self._get_user_id(context, state_info)
        dictionary = {name.casefold(): name for name in TagService().get_user_tags(user_id)}

        if tag is None or tag.casefold() not in dictionary:
            # Подменённый или устаревший payload: тега в справочнике нет
            self._render(
                context,
                state_info,
                helpers.format_invalid_input("Выбери тег из клавиатуры."),
            )
            return

        canonical = dictionary[tag.casefold()]
        key = canonical.casefold()
        selected = list(state_info["data"].get("selected_tags", []))
        if key in {item.casefold() for item in selected}:
            selected = [item for item in selected if item.casefold() != key]
        else:
            selected.append(canonical)

        state_info["data"]["selected_tags"] = selected
        context.set_state(state_info)
        self._render(context, state_info)

    def _handle_text(self, context: BotContext, state_info: dict) -> None:
        user_id = self._get_user_id(context, state_info)
        names = [
            helpers.normalize_tag_name(name)
            for name in (context.text or "").split(",")
            if helpers.normalize_tag_name(name)
        ]
        if not names:
            self._render(
                context,
                state_info,
                helpers.format_invalid_input("Введи теги через запятую или нажми «Готово»."),
            )
            return

        dictionary = {name.casefold(): name for name in TagService().get_user_tags(user_id)}
        selected = list(state_info["data"].get("selected_tags", []))
        existing = {item.casefold() for item in selected}
        for name in names:
            # Новый тег при вводе сохраняет набранную форму, справочник
            # пополняется ею при сохранении книги
            canonical = dictionary.get(name.casefold(), name)
            if canonical.casefold() not in existing:
                existing.add(canonical.casefold())
                selected.append(canonical)

        state_info["data"]["selected_tags"] = selected
        context.set_state(state_info)
        self._render(context, state_info)

    def _handle_page(self, context: BotContext, state_info: dict, action: str) -> None:
        step = 1 if action == "next_page" else -1
        state_info["data"]["tag_page"] = state_info["data"].get("tag_page", 0) + step
        self._render(context, state_info)

    def _handle_done(self, context: BotContext, state_info: dict) -> None:
        selected = sorted(state_info["data"].get("selected_tags", []), key=str.casefold)
        state_info["data"]["selected_tags"] = selected
        self._on_done(context, selected)

    # ── Отрисовка и состояние ───────────────────────────────────────

    def _render(self, context: BotContext, state_info: dict, header: str | None = None) -> None:
        user_id = self._get_user_id(context, state_info)
        tags = TagService().get_user_tags(user_id)

        data = state_info["data"]
        pages = tag_total_pages(len(tags))
        data["tag_page"] = min(max(data.get("tag_page", 0), 0), pages - 1)
        data.setdefault("selected_tags", [])
        context.set_state(state_info)

        selected = data["selected_tags"]
        selection_text = ", ".join(sorted(selected, key=str.casefold)) if selected else "нет"
        message = header or (
            "Выбери теги книги: нажимай кнопки, чтобы отметить или снять тег, "
            "или введи новые через запятую. «Готово» завершает выбор.\n"
            f"\nВыбрано: {selection_text}"
        )
        keyboard = tag_editing_keyboard(tags, selected, data["tag_page"], self._owner_command)
        context.api.messages.send(
            user_id=context.user_id,
            message=message,
            keyboard=keyboard.get_keyboard(),
            random_id=get_random_id(),
        )

    def _get_user_id(self, context: BotContext, state_info: dict) -> str:
        user_id = state_info.get("data", {}).get("user_id")
        if not user_id:
            user = get_or_create_user(context.api, context.user_id)
            user_id = user.id
            state_info.setdefault("data", {})["user_id"] = user_id
            context.set_state(state_info)
        return user_id
