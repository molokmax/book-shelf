from dotenv import load_dotenv
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from utils import logger
from utils.config import load_config
import json

from vk_bot.handlers.start import handle_start_command
from vk_bot.handlers.help import handle_help_command
from vk_bot.handlers.list import handle_list_command
from vk_bot.handlers.stats import handle_stats_command

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
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        command = self.get_command(event)
                        self.logger.debug(f"Получили команду {command} от пользователя {event.user_id}")

                        if command == "/start" or command == "начать":
                            handle_start_command(self.api, event.user_id)
                        elif command == "/help":
                            handle_help_command(self.api, event.user_id)
                        elif command == "/list":
                            handle_list_command(self.api, event.user_id)
                        elif command == "/stats":
                            handle_stats_command(self.api, event.user_id)

            except Exception as e:
                self.logger.error(f"Возникла ошибка при обработке сообщения: {e}")
                self.api.messages.send(user_id=event.user_id, message="Возникла ошибка при обработке сообщения", random_id=0)

    
    def get_command(self, event):
        command = None
        if hasattr(event, 'payload') and event.payload:
            try:
                payload_data = json.loads(event.payload)
                command = payload_data.get('command')
            except Exception as e:
                self.logger.error(f"Возникла ошибка при получении названия команды: {e}")
            
        if not command:
            command = event.text.lower()

        return command
