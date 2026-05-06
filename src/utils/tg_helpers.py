from telegram import Update
from core.models import User
from core.services import UserService


def get_or_create_user(update: Update) -> User:
    """Получает или создаёт пользователя в системе."""
    user_service = UserService()
    if not update.effective_user:
        raise Exception("Current user is not defined")
    
    return user_service.get_or_create_user(
        update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name
    )
