"""Тесты клавиатуры шага выбора тегов."""

import json

from vk_bot.keyboards import TAGS_PER_PAGE, tag_editing_keyboard, tag_total_pages


def keyboard_data(kb):
    raw = kb.get_keyboard()
    return json.loads(raw) if isinstance(raw, str) else raw


def buttons(kb) -> list[dict]:
    return [button for row in keyboard_data(kb)["buttons"] for button in row]


def labels(kb) -> list[str]:
    return [button["action"]["label"] for button in buttons(kb)]


def make_tags(count: int) -> list[str]:
    return [f"tag-{index:02d}" for index in range(count)]


OWNER = "/add"


def test_empty_dictionary_shows_confirm_and_cancel():
    kb = tag_editing_keyboard([], [], 0, OWNER)
    data = keyboard_data(kb)

    assert labels(kb) == ["Готово", "Отмена"]

    rows = data["buttons"]
    assert len(rows) == 1
    assert rows[0][0]["color"] == "positive"
    assert rows[0][1]["color"] == "negative"
    assert json.loads(rows[0][0]["action"]["payload"]) == {"command": OWNER, "action": "done"}
    assert json.loads(rows[0][1]["action"]["payload"]) == {"command": "/cancel"}


def test_tags_laid_out_two_per_row():
    kb = tag_editing_keyboard(make_tags(5), [], 0, OWNER)
    rows = keyboard_data(kb)["buttons"]

    assert [len(row) for row in rows] == [2, 2, 1, 2]
    tag_rows, service_rows = rows[:3], rows[3]
    assert [b["action"]["label"] for row in tag_rows for b in row] == make_tags(5)
    assert [b["action"]["label"] for b in service_rows] == ["Готово", "Отмена"]


def test_tag_button_payload_carries_owner_command():
    kb = tag_editing_keyboard(make_tags(3), [], 0, OWNER)

    for button in buttons(kb):
        action = button["action"]
        label = action["label"]
        if label in ("Готово", "Отмена"):
            continue
        assert json.loads(action["payload"]) == {
            "command": OWNER,
            "action": "toggle",
            "tag": label,
        }


def test_selected_tags_highlighted_primary():
    kb = tag_editing_keyboard(["a", "b", "c"], ["b"], 0, OWNER)

    colors = {button["action"]["label"]: button["color"] for button in buttons(kb)}
    assert colors["a"] == "secondary"
    assert colors["b"] == "primary"
    assert colors["c"] == "secondary"


def test_pagination_second_page_and_buttons():
    tags = make_tags(17)
    first = tag_editing_keyboard(tags, [], 0, OWNER)
    second = tag_editing_keyboard(tags, [], 1, OWNER)

    assert labels(first)[:16] == make_tags(16)
    assert "Ещё →" in labels(first)
    assert "← Назад" not in labels(first)

    # на последней странице только «← Назад»
    assert labels(second) == ["tag-16", "Готово", "Отмена", "← Назад"]

    # Границы клампятся
    clamped = tag_editing_keyboard(tags, [], 99, OWNER)
    assert labels(clamped) == labels(second)


def test_keyboard_within_vk_limits():
    kb = tag_editing_keyboard(make_tags(20), [], 0, OWNER)
    rows = keyboard_data(kb)["buttons"]

    assert len(rows) <= 10
    assert sum(len(row) for row in rows) <= 40
    # 16 тегов + «Готово»/«Отмена» + одна кнопка пагинации (страница первая)
    assert len(rows) == 10
    assert sum(len(row) for row in rows) == 19


def test_tag_named_like_service_button_is_distinct():
    # Тег с именем «Готово» нельзя спутать с кнопкой подтверждения: у тега
    # payload action=toggle, у кнопки done
    kb = tag_editing_keyboard(["Готово", "Отмена"], [], 0, OWNER)

    payload_by_label = {}
    for button in buttons(kb):
        payload = json.loads(button["action"]["payload"])
        payload_by_label.setdefault(button["action"]["label"], []).append(payload)

    assert payload_by_label["Готово"][0]["action"] == "toggle"
    assert payload_by_label["Готово"][1]["action"] == "done"
    assert payload_by_label["Отмена"][0]["action"] == "toggle"
    assert payload_by_label["Отмена"][1] == {"command": "/cancel"}


def test_tag_total_pages_helper():
    assert tag_total_pages(0) == 1
    assert tag_total_pages(1) == 1
    assert tag_total_pages(TAGS_PER_PAGE) == 1
    assert tag_total_pages(TAGS_PER_PAGE + 1) == 2
