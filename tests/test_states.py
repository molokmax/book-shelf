"""Инвентарь состояний: общие шаги совпадают у флоу и сценариев."""

from vk_bot.states import (
    AddState,
    DetailsState,
    EditState,
    ListState,
    ProgressScenarioState,
    ProgressState,
    SelectionState,
    TagState,
)


def values(state_enum):
    return {member.value for member in state_enum}


def test_selection_states_are_shared_by_scenarios():
    selection = values(SelectionState)
    assert selection <= values(EditState)
    assert selection <= values(DetailsState)
    assert selection <= values(ProgressScenarioState)
    assert SelectionState.CHOOSE_FILTER.value in values(ListState)


def test_tag_state_is_shared_by_add_and_edit():
    assert TagState.SELECTING_TAGS.value in values(AddState)
    assert TagState.SELECTING_TAGS.value in values(EditState)


def test_progress_states_are_shared_with_scenario():
    assert values(ProgressState) <= values(ProgressScenarioState)


def test_state_values_are_unique_inside_enum():
    for state_enum in (
        SelectionState,
        TagState,
        ProgressState,
        AddState,
        EditState,
        DetailsState,
        ListState,
        ProgressScenarioState,
    ):
        members = [member.value for member in state_enum]
        assert len(members) == len(set(members))
