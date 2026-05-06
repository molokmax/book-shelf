from dotenv import load_dotenv
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType
from utils import logger
from utils.config import load_config
import json

from vk_bot.handlers.start import handle_start_command
from vk_bot.handlers.help import handle_help_command

class VkBookShelfBot:

    def __init__(self) -> None:
        load_dotenv()
        self.logger = logger.setup_logger(__name__)
        self.config = load_config()

    def setup(self):
        self.logger.info("Инициализация бота...")
        token = self.config.vk_bot_token
        vk = VkApi(token=token)
        self.api = vk.get_api()
        return VkLongPoll(vk)

    def run(self) -> None:
        """Start the VK bot."""
        longpoll = self.setup()        
        self.logger.info("Бот запущен и ожидает сообщений...")
        for event in longpoll.listen():
            try:
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        command = self.get_command(event)

                        if command == "/start" or command == "начать":
                            handle_start_command(self.api, event.user_id)
                        elif command == "/help":
                            handle_help_command(self.api, event.user_id)

            except Exception as e:
                self.logger.error(f"Возникла ошибка при обработке сообщения: {e}")

    
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
