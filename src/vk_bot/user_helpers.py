"""Utility functions for VK bot user management."""

from vk_api.vk_api import VkApiMethod

from core.models import User
from core.services import UserService


def get_or_create_user(vk: VkApiMethod, vk_user_id: int):
    """Retrieve an existing user by VK user ID or create a new one."""
    user_service = UserService()
    return user_service.get_or_create_user(vk_user_id, lambda user_id: __create_user(vk, user_id))


def __create_user(vk: VkApiMethod, vk_user_id: int):
    vk_user = vk.users.get(user_ids=[vk_user_id], fields=["screen_name"])[0]
    user = User(
        external_id=vk_user_id,
        username=vk_user["screen_name"],
        first_name=vk_user["first_name"],
        last_name=vk_user["last_name"],
    )
    return user
