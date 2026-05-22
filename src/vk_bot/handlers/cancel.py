from vk_api.utils import get_random_id
from vk_api.vk_api import VkApiMethod

from vk_bot.keyboards import main_keyboard
from vk_bot.states import active_states


def handle_cancel_command(vk: VkApiMethod, user_id: int) -> None:
    """Обработчик команды /cancel."""
    if user_id in active_states:
        del active_states[user_id]

    vk.messages.send(
        user_id=user_id,
        message="Операция отменена",
        keyboard=main_keyboard().get_keyboard(),
        random_id=get_random_id(),
    )
