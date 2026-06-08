"""Export command handler as AbstractCommandHandler subclass.

Содержит полную реализацию команды /export.
"""

from typing import Any

from vk_api.utils import get_random_id

from core.services import BookService
from utils.export import export_to_csv
from vk_bot.user_helpers import get_or_create_user

from ..context import BotContext
from .base import AbstractCommandHandler


class ExportHandler(AbstractCommandHandler):
    """Handler for the `/export` command.

    Генерирует CSV-файл со списком книг пользователя и загружает его в VK.
    """

    priority = 10
    commands = ["/export", "export"]

    def handle(self, context: BotContext) -> Any:
        api = context.api
        user_id = context.user_id
        user = get_or_create_user(api, user_id)

        book_service = BookService()
        books = book_service.get_all_books(user.id)

        csv_path = export_to_csv(books, user.id)

        upload_resp = context.upload.document_message(
            str(csv_path), title="books.csv", peer_id=context.peer_id
        )
        csv_path.unlink(missing_ok=True)
        doc = upload_resp["doc"]
        attach = f'doc{doc["owner_id"]}_{doc["id"]}'
        api.messages.send(
            user_id=user_id,
            message="Список книг готов",
            attachment=attach,
            random_id=get_random_id(),
        )
        return True
