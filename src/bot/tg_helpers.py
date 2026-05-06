from telegram import Update, User as TgUser
from core.models import User
from core.services import UserService


def get_or_create_user(update: Update) -> User:
    """Получает или создаёт пользователя в системе."""
    user_service = UserService()
    tg_user = update.effective_user
    if not tg_user:
        raise Exception("Не удалось определить текущего пользователя")
    
    user_factory = lambda user_id: __create_user(tg_user, user_id)
    return user_service.get_or_create_user(tg_user.id, user_factory)

def __create_user(tg_user: TgUser, user_id):
    return User(
        external_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name
    )
