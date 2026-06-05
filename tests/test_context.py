import json
from unittest.mock import MagicMock


def make_fake_event(user_id=123, peer_id=456, text="hello", payload_str=None):
    event = MagicMock()
    event.user_id = user_id
    event.peer_id = peer_id
    event.text = text
    event.payload = payload_str
    return event


def make_context(event=None, vk=None, upload=None):
    if event is None:
        event = make_fake_event()
    if vk is None:
        vk = MagicMock()
        vk.get_api.return_value = MagicMock()
    if upload is None:
        upload = MagicMock()
    from vk_bot.context import BotContext

    return BotContext(vk=vk, upload=upload, event=event)


def test_constructor_stores_attributes():
    vk = MagicMock()
    upload = MagicMock()
    event = make_fake_event()
    ctx = make_context(vk=vk, upload=upload, event=event)

    assert ctx.vk is vk
    assert ctx.upload is upload
    assert ctx.event is event


def test_api_derived_from_vk():
    fake_api = MagicMock()
    vk = MagicMock()
    vk.get_api.return_value = fake_api
    ctx = make_context(vk=vk)

    assert ctx.api is fake_api
    vk.get_api.assert_called_once()


def test_properties_delegate_to_event():
    event = make_fake_event(user_id=123, peer_id=456, text="hello")
    ctx = make_context(event=event)

    assert ctx.user_id == 123
    assert ctx.peer_id == 456
    assert ctx.text == "hello"


def test_payload_parses_json():
    payload_data = {"command": "/cancel", "status": "reading"}
    event = make_fake_event(payload_str=json.dumps(payload_data))
    ctx = make_context(event=event)

    assert ctx.payload == payload_data


def test_payload_returns_empty_dict_when_none():
    event = make_fake_event(payload_str=None)
    ctx = make_context(event=event)

    assert ctx.payload == {}


def test_payload_returns_empty_dict_when_empty_string():
    event = make_fake_event(payload_str="")
    ctx = make_context(event=event)

    assert ctx.payload == {}


def test_command_from_payload():
    event = make_fake_event(text="some text", payload_str=json.dumps({"command": "/cancel"}))
    ctx = make_context(event=event)

    assert ctx.command == "/cancel"


def test_command_from_text_fallback():
    event = make_fake_event(text="/Add Book")
    ctx = make_context(event=event)

    assert ctx.command == "/add book"


def test_command_lowercases_text():
    event = make_fake_event(text="/Start Here")
    ctx = make_context(event=event)

    assert ctx.command == "/start here"


def test_immutable_vk():
    ctx = make_context()
    try:
        ctx.vk = "new_value"
        assert False, "Expected AttributeError"
    except AttributeError:
        pass


def test_immutable_upload():
    ctx = make_context()
    try:
        ctx.upload = "new_value"
        assert False, "Expected AttributeError"
    except AttributeError:
        pass


def test_immutable_event():
    ctx = make_context()
    try:
        ctx.event = "new_value"
        assert False, "Expected AttributeError"
    except AttributeError:
        pass
