from unittest.mock import patch, MagicMock
from pathlib import Path

# Helper to create a fake Vk instance


def make_fake_vk():
    class FakeVk:
        def __init__(self):
            self.sent_messages = []
            # vk.messages should have a send method
            self.messages = self
            # users.get is used inside handler
            self.users = MagicMock()
            self.users.get.return_value = [
                {
                    "screen_name": "test_user",
                    "first_name": "Test",
                    "last_name": "User",
                }
            ]

        def send(self, user_id, message, attachment=None, random_id=None, **kwargs):
            # Record parameters for verification
            self.sent_messages.append(
                {
                    "user_id": user_id,
                    "message": message,
                    "attachment": attachment,
                    "random_id": random_id,
                    **kwargs,
                }
            )

    return FakeVk()


def test_handle_export_sends_csv_and_message():
    fake_vk = make_fake_vk()
    chat_id = 999
    user_id = 123

    # Fake books – the export logic only iterates over them
    fake_books = [MagicMock(), MagicMock()]

    # Mock user returned by get_or_create_user
    mock_user = MagicMock()
    mock_user.id = "user-123"

    # Mock path returned by export_to_csv
    mock_path = MagicMock(spec=Path)
    mock_path.__str__.return_value = "/tmp/user-123_123456.csv"
    mock_path.unlink.return_value = None

    # Mock upload object
    upload_resp = {"doc": {"owner_id": 10, "id": 20}}
    fake_upload = MagicMock()
    fake_upload.document_message.return_value = upload_resp

    # Patch dependencies used inside the handler
    with (
        patch("vk_bot.handlers.export.get_or_create_user", return_value=mock_user),
        patch("vk_bot.handlers.export.BookService") as MockBookService,
        patch(
            "vk_bot.handlers.export.export_to_csv", return_value=mock_path
        ) as mock_export_to_csv,
    ):
        # Configure BookService instance
        MockBookService.return_value.get_all_books.return_value = fake_books

        # Import handler after patches are applied
        from vk_bot.handlers.export import handle_export_command

        # Execute the handler
        handle_export_command(
            vk=fake_vk, user_id=user_id, upload=fake_upload, chat_id=chat_id
        )

    # Verify export_to_csv called with expected arguments
    mock_export_to_csv.assert_called_once_with(fake_books, mock_user.id)

    # Verify document was uploaded and the temporary file removed
    fake_upload.document_message.assert_called_once_with(
        str(mock_path), title="books.csv", peer_id=chat_id
    )
    mock_path.unlink.assert_called_once_with(missing_ok=True)

    # Verify a message was sent to the user with correct attachment format
    assert len(fake_vk.sent_messages) == 1
    sent = fake_vk.sent_messages[0]
    assert sent["user_id"] == user_id
    assert "Список книг готов" in sent["message"]
    expected_attach = f"doc{upload_resp['doc']['owner_id']}_{upload_resp['doc']['id']}"
    assert sent["attachment"] == expected_attach


def test_handle_export_with_no_books_creates_empty_csv():
    fake_vk = make_fake_vk()
    user_id = 456
    chat_id = 321

    mock_user = MagicMock()
    mock_user.id = "user-456"

    mock_path = MagicMock(spec=Path)
    mock_path.__str__.return_value = "/tmp/empty.csv"
    mock_path.unlink.return_value = None

    fake_upload = MagicMock()
    fake_upload.document_message.return_value = {"doc": {"owner_id": 1, "id": 2}}

    with (
        patch("vk_bot.handlers.export.get_or_create_user", return_value=mock_user),
        patch("vk_bot.handlers.export.BookService") as MockBookService,
        patch("vk_bot.handlers.export.export_to_csv", return_value=mock_path),
    ):
        MockBookService.return_value.get_all_books.return_value = []
        from vk_bot.handlers.export import handle_export_command

        handle_export_command(
            vk=fake_vk, user_id=user_id, upload=fake_upload, chat_id=chat_id
        )

    # A message should still be sent even if no books
    assert len(fake_vk.sent_messages) == 1
    sent = fake_vk.sent_messages[0]
    assert "Список книг готов" in sent["message"]
    expected_attach = "doc1_2"
    assert sent["attachment"] == expected_attach
