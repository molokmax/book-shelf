from vk_api.keyboard import VkKeyboard

def start_keyboard() -> VkKeyboard:
    """Create the keyboard for the /start command."""
    kb = VkKeyboard()
    kb.add_button('/add')
    kb.add_button('/list')
    kb.add_button('/edit')
    kb.add_button('/stats')
    kb.add_button('/help')
    return kb

def cancel_keyboard() -> VkKeyboard:
    kb = VkKeyboard()
    kb.add_button('Отмена', payload={'command': '/cancel'})
    return kb