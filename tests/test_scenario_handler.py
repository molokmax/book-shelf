"""Тесты каркаса многошагового сценария ScenarioHandler."""

from enum import StrEnum

import pytest
from conftest import FakeStateStorage
from conftest import FakeVkApi as FakeVkApiMethod
from conftest import make_context

from vk_bot.handlers.scenario import ScenarioHandler


class DemoState(StrEnum):
    FIRST = "first"
    SECOND = "second"
    THIRD = "third"


class DemoHandler(ScenarioHandler):
    priority = 10
    commands = ["/demo"]
    scenario_command = "/demo"
    initial_state = DemoState.FIRST
    states = DemoState

    def start(self, context):
        self.begin(context, DemoState.FIRST, {"value": ""})

    def render_first(self, context, state_info):
        context.send_message("first prompt")

    def step_first(self, context, state_info):
        if context.text.strip() == "stay":
            return None
        state_info["data"]["value"] = context.text
        return DemoState.SECOND

    def render_second(self, context, state_info):
        context.send_message(f"second prompt: {state_info['data']['value']}")

    def step_second(self, context, state_info):
        if context.text.strip() == "next":
            state_info["data"]["note"] = "from second"
            return DemoState.THIRD
        self.finish(context, "done")
        return None

    def render_third(self, context, state_info):
        context.send_message("third prompt")

    def step_third(self, context, state_info):
        self.finish(context, "done")
        return None


def test_entry_creates_state_and_sends_prompt():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    result = DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))

    assert result is True
    state = storage.get(1)
    assert state["command"] == "/demo"
    assert state["state"] == "first"
    assert state["data"]["value"] == ""
    assert fake_api.sent_messages[-1]["message"] == "first prompt"


def test_transition_saves_data_and_renders_next_step():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "Название", storage=storage))

    assert storage.get(1)["state"] == "second"
    assert storage.get(1)["data"]["value"] == "Название"
    assert fake_api.sent_messages[-1]["message"] == "second prompt: Название"


def test_step_without_transition_stays_in_state():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "stay", storage=storage))

    assert storage.get(1)["state"] == "first"
    assert fake_api.sent_messages[-1]["message"] == "first prompt"


def test_finish_sends_message_before_deleting_state():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "Название", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "любой текст", storage=storage))

    assert fake_api.sent_messages[-1]["message"] == "done"
    assert fake_api.deleted_ids == [1, 2]  # удалены промпты шагов, финал остался
    assert not storage.is_active(1)


def test_unknown_state_resets_scenario():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()
    storage.save(1, {"command": "/demo", "state": "nope", "data": {}})

    DemoHandler().handle(make_context(fake_api, 1, "текст", storage=storage))

    assert "Не удалось продолжить сценарий" in fake_api.sent_messages[-1]["message"]
    assert "/demo" in fake_api.sent_messages[-1]["message"]
    assert not storage.is_active(1)


def test_repeated_command_restarts_scenario():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "Название", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))

    assert storage.get(1)["state"] == "first"
    assert storage.get(1)["data"]["value"] == ""
    assert fake_api.sent_messages[-1]["message"] == "first prompt"


def test_payload_action_does_not_restart_scenario():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    DemoHandler().handle(
        make_context(
            fake_api,
            1,
            "",
            payload={"command": "/demo", "action": "toggle"},
            storage=storage,
        )
    )

    assert storage.get(1)["state"] == "second"


def test_alias_without_slash_does_not_restart_scenario():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "demo", storage=storage))

    assert storage.get(1)["state"] == "second"
    assert storage.get(1)["data"]["value"] == "demo"


# ── Кнопка «Назад» (issue #59) ──────────────────────────────────────


def make_back_context(fake_api, storage, user_id=1):
    return make_context(
        fake_api,
        user_id,
        "",
        payload={"command": "/demo", "action": "back"},
        storage=storage,
    )


def test_back_restores_previous_step_and_rerenders_prompt():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "Название", storage=storage))
    DemoHandler().handle(make_back_context(fake_api, storage))

    state = storage.get(1)
    assert state["state"] == "first"
    assert state["history"] == []
    assert fake_api.sent_messages[-1]["message"] == "first prompt"


def test_back_restores_data_snapshot_and_discards_later_input():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "Название", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "next", storage=storage))
    assert storage.get(1)["state"] == "third"
    assert storage.get(1)["data"]["note"] == "from second"

    # Возврат к second: введённое на second сохранилось в снимке
    DemoHandler().handle(make_back_context(fake_api, storage))
    state = storage.get(1)
    assert state["state"] == "second"
    assert state["data"]["value"] == "Название"
    assert state["data"]["note"] == "from second"
    assert fake_api.sent_messages[-1]["message"] == "second prompt: Название"

    # Возврат к first: данные «будущих» шагов отброшены, ввод заново
    DemoHandler().handle(make_back_context(fake_api, storage))
    state = storage.get(1)
    assert state["state"] == "first"
    assert "note" not in state["data"]

    DemoHandler().handle(make_context(fake_api, 1, "Другое", storage=storage))
    assert storage.get(1)["data"]["value"] == "Другое"
    assert "note" not in storage.get(1)["data"]


def test_history_snapshot_excludes_last_message_id():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "Название", storage=storage))

    history = storage.get(1)["history"]
    assert len(history) == 1
    assert history[0]["state"] == "first"
    assert "last_message_id" not in history[0]["data"]


def test_step_without_transition_does_not_grow_history():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "stay", storage=storage))

    assert storage.get(1).get("history", []) == []


def test_back_on_first_step_is_noop():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    messages_before = len(fake_api.sent_messages)
    DemoHandler().handle(make_back_context(fake_api, storage))

    assert storage.get(1)["state"] == "first"
    assert len(fake_api.sent_messages) == messages_before


def test_stale_back_does_not_restart_scenario():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_back_context(fake_api, storage))

    assert fake_api.sent_messages[-1]["message"] == "Сценарий уже завершён."
    assert not storage.is_active(1)


def test_restart_clears_history():
    fake_api = FakeVkApiMethod()
    storage = FakeStateStorage()

    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "Название", storage=storage))
    DemoHandler().handle(make_context(fake_api, 1, "/demo", storage=storage))

    assert storage.get(1).get("history", []) == []
    DemoHandler().handle(make_back_context(fake_api, storage))
    assert storage.get(1)["state"] == "first"


def test_missing_step_method_fails_on_import():
    with pytest.raises(TypeError, match="step_second"):

        class BrokenHandler(ScenarioHandler):
            commands = ["/broken"]
            scenario_command = "/broken"
            initial_state = DemoState.FIRST
            states = DemoState

            def step_first(self, context, state_info):
                return None
