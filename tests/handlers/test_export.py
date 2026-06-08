import json
from pathlib import Path
from unittest.mock import MagicMock, patch


def make_context(api, upload, user_id, peer_id):
    vk = MagicMock()
    vk.get_api.return_value = api
    event = MagicMock()
    event.user_id = user_id
    event.peer_id = peer_id
    event.text = "/export"
    event.payload = None
    from vk_bot.context import BotContext

    return BotContext(vk=vk, upload=upload, event=event)


def make_fake_vk():
    class FakeVk:
        def __init__(self):
            self.sent_messages = []
            self.messages = self

        def send(self, **kwargs):
            self.sent_messages.append(kwargs)

    return FakeVk()


def test_handle_export_sends_csv_and_message():
    fake_api = make_fake_vk()
    chat_id = 999
    user_id = 123

    fake_books = [MagicMock(), MagicMock()]

    mock_user = MagicMock()
    mock_user.id = "user-123"

    mock_path = MagicMock(spec=Path)
    mock_path.__str__.return_value = "/tmp/user-123_123456.csv"
    mock_path.unlink.return_value = None

    upload_resp = {"doc": {"owner_id": 10, "id": 20}}
    fake_upload = MagicMock()
    fake_upload.document_message.return_value = upload_resp

    ctx = make_context(fake_api, fake_upload, user_id, chat_id)

    with (
        patch("vk_bot.handlers.export.get_or_create_user", return_value=mock_user),
        patch("vk_bot.handlers.export.BookService") as MockBookService,
        patch(
            "vk_bot.handlers.export.export_to_csv", return_value=mock_path
        ) as mock_export_to_csv,
    ):
        MockBookService.return_value.get_all_books.return_value = fake_books
        from vk_bot.handlers.export import ExportHandler

        ExportHandler().handle(ctx)

    mock_export_to_csv.assert_called_once_with(fake_books, mock_user.id)
    fake_upload.document_message.assert_called_once_with(
        str(mock_path), title="books.csv", peer_id=chat_id
    )
    mock_path.unlink.assert_called_once_with(missing_ok=True)

    assert len(fake_api.sent_messages) == 1
    sent = fake_api.sent_messages[0]
    assert sent["user_id"] == user_id
    assert "Список книг готов" in sent["message"]
    expected_attach = f"doc{upload_resp['doc']['owner_id']}_{upload_resp['doc']['id']}"
    assert sent["attachment"] == expected_attach


def test_handle_export_with_no_books_creates_empty_csv():
    fake_api = make_fake_vk()
    user_id = 456
    chat_id = 321

    mock_user = MagicMock()
    mock_user.id = "user-456"

    mock_path = MagicMock(spec=Path)
    mock_path.__str__.return_value = "/tmp/empty.csv"
    mock_path.unlink.return_value = None

    fake_upload = MagicMock()
    fake_upload.document_message.return_value = {"doc": {"owner_id": 1, "id": 2}}

    ctx = make_context(fake_api, fake_upload, user_id, chat_id)

    with (
        patch("vk_bot.handlers.export.get_or_create_user", return_value=mock_user),
        patch("vk_bot.handlers.export.BookService") as MockBookService,
        patch("vk_bot.handlers.export.export_to_csv", return_value=mock_path),
    ):
        MockBookService.return_value.get_all_books.return_value = []
        from vk_bot.handlers.export import ExportHandler

        ExportHandler().handle(ctx)

    assert len(fake_api.sent_messages) == 1
    sent = fake_api.sent_messages[0]
    assert "Список книг готов" in sent["message"]
    expected_attach = "doc1_2"
    assert sent["attachment"] == expected_attach
