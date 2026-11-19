"""Тесты кнопки «Назад» в общих клавиатурах (issue #59)."""

import json

from vk_bot.keyboards import (
    cancel_keyboard,
    filter_keyboard,
    status_keyboard,
    tag_editing_keyboard,
    tags_keyboard,
)


def keyboard_data(kb):
    raw = kb.get_keyboard()
    return json.loads(raw) if isinstance(raw, str) else raw


def buttons(kb) -> list[dict]:
    return [button for row in keyboard_data(kb)["buttons"] for button in row]


def labels(kb) -> list[str]:
    return [button["action"]["label"] for button in buttons(kb)]


def back_payloads(kb) -> list[dict]:
    return [
        json.loads(button["action"]["payload"])
        for button in buttons(kb)
        if button["action"]["label"] == "Назад"
    ]


def test_cancel_keyboard_with_back():
    kb = cancel_keyboard("/add")

    assert labels(kb) == ["Отмена", "Назад"]
    assert back_payloads(kb) == [{"command": "/add", "action": "back"}]


def test_cancel_keyboard_without_back_by_default():
    assert labels(cancel_keyboard()) == ["Отмена"]


def test_filter_keyboard_with_back():
    kb = filter_keyboard("/edit")

    assert "Назад" in labels(kb)
    assert back_payloads(kb) == [{"command": "/edit", "action": "back"}]


def test_status_keyboard_with_back():
    kb = status_keyboard("/list")

    assert "Назад" in labels(kb)
    assert back_payloads(kb) == [{"command": "/list", "action": "back"}]


def test_tags_keyboard_with_back():
    kb = tags_keyboard(["a", "b"], "/details")

    assert "Назад" in labels(kb)
    assert back_payloads(kb) == [{"command": "/details", "action": "back"}]


def test_tag_editing_back_in_service_row():
    kb = tag_editing_keyboard(["a", "b"], [], 0, "/add", back_command="/add")
    rows = keyboard_data(kb)["buttons"]

    service_row = rows[-1]
    assert [button["action"]["label"] for button in service_row] == [
        "Готово",
        "Отмена",
        "Назад",
    ]
    assert back_payloads(kb) == [{"command": "/add", "action": "back"}]


def test_tag_editing_back_coexists_with_pagination():
    tags = [f"tag-{index:02d}" for index in range(20)]
    kb = tag_editing_keyboard(tags, [], 1, "/add", back_command="/add")

    # Пагинация и возврат к предыдущему шагу — разные кнопки и payload
    assert "← Страница" in labels(kb)
    assert "Назад" in labels(kb)
    assert back_payloads(kb) == [{"command": "/add", "action": "back"}]

    rows = keyboard_data(kb)["buttons"]
    assert len(rows) <= 10
    assert sum(len(row) for row in rows) <= 40
