from dotenv import load_dotenv
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from utils import logger
from utils.config import load_config
import json

from vk_bot.states import active_states
from vk_bot.handlers.start import handle_start_command
from vk_bot.handlers.help import handle_help_command
from vk_bot.handlers.list import handle_list_command
from vk_bot.handlers.stats import handle_stats_command
from vk_bot.handlers.add import handle_add_command
from vk_bot.handlers.add import handle_add_command_step
from vk_bot.handlers.edit import handle_edit_command, handle_edit_command_step
from vk_bot.handlers.cancel import handle_cancel_command

class VkBookShelfBot:

    def __init__(self) -> None:
        load_dotenv()
        self.logger = logger.setup_logger(__name__)
        self.config = load_config()

    def create_longpoll(self):
        self.logger.info("Инициализация бота...")
        token = self.config.vk_bot_token
        vk = VkApi(token=token)
        self.api = vk.get_api()
        return VkLongPoll(vk)

    def run(self) -> None:
        """Start the VK bot."""
        longpoll = self.create_longpoll()        
        self.logger.info("Бот запущен и ожидает сообщений...")
        for event in longpoll.listen():
            try:
                if event.type != VkEventType.MESSAGE_NEW:
                    continue
                if not event.to_me:
                    continue
                if not event.user_id:
                    self.logger.warning("Сообщение не будет обработано так как неизвестен идентификатор текущего пользователя")
                    continue

                command = self.get_command(event)
                self.logger.debug(f"Получили команду {command} от пользователя {event.user_id}")

                # TODO: В какие моменты нужно сбратывать текущий стейт?
                # TODO: реализовать механизм роутинга
                if command == "/cancel" or command == "отмена":
                    handle_cancel_command(self.api, event.user_id)
                elif command == "/start" or command == "начать":
                    handle_start_command(self.api, event.user_id)
                elif command == "/help":
                    handle_help_command(self.api, event.user_id)
                elif command == "/list":
                    handle_list_command(self.api, event.user_id)
                elif command == "/stats":
                    handle_stats_command(self.api, event.user_id)
                elif command == "/add":
                    handle_add_command(self.api, event.user_id)
                elif command == "/edit":
                    handle_edit_command(self.api, event.user_id)
                elif event.user_id in active_states:
                    state_info = active_states[event.user_id]
                    state_command = state_info["command"]
                    if state_command == "/add":
                        handle_add_command_step(self.api, event.user_id, event.text)
                    elif state_command == "/edit":
                        handle_edit_command_step(self.api, event.user_id, event.text)
                    else:
                        # TODO: Обработать отсутствие обработчика команды
                        pass

            except Exception as e:
                self.logger.error(f"Возникла ошибка при обработке сообщения: {e}")
                self.api.messages.send(user_id=event.user_id, message="Возникла ошибка при обработке сообщения", random_id=get_random_id())

    def get_payload(self, event):
        if hasattr(event, 'payload') and event.payload:
            return json.loads(event.payload)
        else:
            return {}
    
    def get_command(self, event):
        command = None
        try:
            command = self.get_payload(event).get('command')
        except Exception as e:
            self.logger.error(f"Возникла ошибка при получении названия команды: {e}")
        
        if not command:
            command = event.text.lower()

        return command
