import time

from dotenv import load_dotenv
from vk_api import ApiError, VkApi
from vk_api.longpoll import Event, VkEventType, VkLongPoll
from vk_api.upload import VkUpload
from vk_api.utils import get_random_id

from core.storage import ActiveStateStorage
from utils import logger
from utils.config import load_config
from vk_bot.command_router import CommandRouter
from vk_bot.context import BotContext
from vk_bot.handlers.add import AddHandler
from vk_bot.handlers.cancel import CancelHandler
from vk_bot.handlers.details import DetailsHandler
from vk_bot.handlers.edit import EditHandler
from vk_bot.handlers.export import ExportHandler
from vk_bot.handlers.help import HelpHandler
from vk_bot.handlers.list import ListHandler
from vk_bot.handlers.start import StartHandler
from vk_bot.handlers.stats import StatsHandler


class VkBookShelfBot:

    def __init__(self) -> None:
        load_dotenv()
        self.logger = logger.setup_logger(__name__)
        self.config = load_config()
        self._state_storage = ActiveStateStorage()
        # Инициализируем роутер команд и регистрируем обработчики
        self.router = CommandRouter()
        self.router.register_handler(StartHandler())
        self.router.register_handler(CancelHandler())
        self.router.register_handler(AddHandler())
        self.router.register_handler(EditHandler())
        self.router.register_handler(ListHandler())
        self.router.register_handler(DetailsHandler())
        self.router.register_handler(ExportHandler())
        self.router.register_handler(HelpHandler())
        self.router.register_handler(StatsHandler())

    def create_longpoll(self):
        self.logger.info("Инициализация бота...")
        token = self.config.bot_token
        self.vk = VkApi(token=token)
        self.api = self.vk.get_api()
        self.upload = VkUpload(self.vk)
        return VkLongPoll(self.vk)

    def run(self) -> None:
        """Start the VK bot."""
        while True:
            try:
                self.logger.info("Бот запущен и выполняет подключение...")
                longpoll = self.create_longpoll()
                self.logger.info("Бот запущен и ожидает сообщений...")
                for event in longpoll.listen():
                    self.handle_event(event)

            except ApiError as e:
                # Специфичная ошибка VK API
                self.logger.error("[Ошибка VK API] Код: %s. Сообщение: %s", e.code, e)
                if e.code == 5:  # Авторизация сломалась
                    self.logger.error("Неверный токен. Проверьте его.")
                    time.sleep(60)
                else:
                    time.sleep(5)

            except (ConnectionError, TimeoutError) as e:
                # Ошибки сети
                self.logger.error(f"[Сетевая ошибка] {e}. Переподключение через 10 сек...")
                time.sleep(10)

            except Exception as e:
                # Любая другая неожиданная ошибка
                self.logger.critical(f"[Критическая ошибка] {e}. Перезапуск через 30 сек...")
                time.sleep(30)

    def handle_event(self, event: Event):
        try:
            if event.type != VkEventType.MESSAGE_NEW:
                return
            if not event.to_me:
                return
            if not event.user_id:
                self.logger.warning(
                    "Сообщение не будет обработано: " "неизвестен идентификатор пользователя"
                )
                return
            if not event.peer_id:
                self.logger.warning(
                    "Сообщение не будет обработано: " "неизвестен идентификатор чата"
                )
                return

            context = BotContext(
                vk=self.vk,
                upload=self.upload,
                event=event,
                storage=self._state_storage,
            )
            self.logger.debug(
                "Получили команду %s от пользователя %s",
                context.command,
                context.user_id,
            )

            # Маршрутизация через CommandRouter (включая роутинг по стейту)
            routed = self.router.route(context)
            if routed is not None:
                return

        except Exception as e:
            self.logger.error(f"Возникла ошибка при обработке сообщения: {e}")
            self.api.messages.send(
                user_id=event.user_id,
                message="Возникла ошибка при обработке сообщения",
                random_id=get_random_id(),
            )
