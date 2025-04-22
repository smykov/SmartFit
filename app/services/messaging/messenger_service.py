from typing import Dict, Any, List, Optional
import logging

from app.services.messaging.message_interface import IMessageService
from app.services.messaging.whatsapp_service import WhatsAppService
from app.services.messaging.telegram_service import TelegramService
from app.db.interfaces.user_repository_interface import IUserRepository

logger = logging.getLogger(__name__)


class MessengerService(IMessageService):
    """
    Фасадный сервис для работы с разными мессенджерами.
    Выбирает соответствующий сервис в зависимости от типа мессенджера.
    """

    def __init__(
            self,
            whatsapp_service: WhatsAppService,
            telegram_service: TelegramService,
            user_repository: IUserRepository
    ):
        """
        Инициализация фасадного сервиса

        Args:
            whatsapp_service: Сервис WhatsApp
            telegram_service: Сервис Telegram
            user_repository: Репозиторий пользователей
        """
        self.whatsapp_service = whatsapp_service
        self.telegram_service = telegram_service
        self.user_repository = user_repository
        self.logger = logging.getLogger(self.__class__.__name__)

    async def initialize(self):
        """Инициализация всех сервисов мессенджеров"""
        await self.whatsapp_service.initialize()
        await self.telegram_service.initialize()

    async def get_preferred_service(self, user_id: Optional[str],
                                    messenger_type: Optional[str] = None) -> IMessageService:
        """
        Определяет предпочитаемый сервис мессенджера для пользователя

        Args:
            user_id: ID пользователя
            messenger_type: Тип мессенджера (если задан явно)

        Returns:
            IMessageService: Соответствующий сервис мессенджера
        """
        if messenger_type:
            # Используем явно указанный тип
            return self._get_service_by_type(messenger_type)

        if user_id:
            # Получаем предпочтения пользователя
            user = await self.user_repository.get_by_id(user_id)
            if user and "preferred_messenger" in user:
                return self._get_service_by_type(user["preferred_messenger"])

        # По умолчанию используем WhatsApp
        return self.whatsapp_service

    def _get_service_by_type(self, messenger_type: str) -> IMessageService:
        """
        Возвращает сервис по типу мессенджера

        Args:
            messenger_type: Тип мессенджера ('whatsapp' или 'telegram')

        Returns:
            IMessageService: Соответствующий сервис
        """
        if messenger_type.lower() == 'telegram':
            return self.telegram_service

        # По умолчанию возвращаем WhatsApp
        return self.whatsapp_service

    async def send_message(self, to_phone: str, message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет текстовое сообщение через соответствующий мессенджер

        Args:
            to_phone: Идентификатор получателя
            message: Текст сообщения
            context: Контекст сообщения

        Returns:
            bool: Результат отправки
        """
        try:
            # Определяем тип мессенджера из контекста или user_id
            messenger_type = context.get('messenger_type') if context else None
            user_id = context.get('user_id') if context else None

            service = await self.get_preferred_service(user_id, messenger_type)
            return await service.send_message(to_phone, message, context)
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            return False

    async def send_messages(self, to_phone: str, messages: List[str], context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет несколько текстовых сообщений последовательно через соответствующий мессенджер

        Args:
            to_phone: Идентификатор получателя
            messages: Список текстовых сообщений
            context: Контекст сообщений

        Returns:
            bool: Результат отправки (True, если все сообщения отправлены успешно)
        """
        try:
            # Определяем тип мессенджера из контекста или user_id
            messenger_type = context.get('messenger_type') if context else None
            user_id = context.get('user_id') if context else None

            service = await self.get_preferred_service(user_id, messenger_type)
            return await service.send_messages(to_phone, messages, context)
        except Exception as e:
            self.logger.error(f"Error sending multiple messages: {str(e)}")
            return False

    async def send_template_message(self, to_phone: str, template_name: str, user_id: Optional[str] = None,
                                    params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет шаблонное сообщение через соответствующий мессенджер

        Args:
            to_phone: Идентификатор получателя
            template_name: Название шаблона
            user_id: ID пользователя для определения языка
            params: Параметры для шаблона

        Returns:
            bool: Результат отправки
        """
        try:
            # Определяем предпочитаемый мессенджер пользователя
            service = await self.get_preferred_service(user_id)

            # Создаем контекст для шаблонного сообщения
            context = {
                "template_name": template_name,
                "template_params": params,
                "user_id": user_id
            }

            return await service.send_template_message(to_phone, template_name, user_id, params)
        except Exception as e:
            self.logger.error(f"Error sending template message: {str(e)}")
            return False

    async def can_send_reminder(self, phone_number: str, reminder_type: str, min_interval_seconds: int) -> bool:
        """
        Проверяет, можно ли отправить напоминание определенного типа

        Args:
            phone_number: Номер телефона пользователя
            reminder_type: Тип напоминания
            min_interval_seconds: Минимальный интервал между напоминаниями в секундах

        Returns:
            bool: True, если можно отправить напоминание
        """
        try:
            # Пытаемся получить пользователя по номеру телефона
            user = await self.user_repository.get_by_phone(phone_number)

            if not user:
                return False

            # Используем предпочитаемый сервис пользователя
            service = await self.get_preferred_service(user.get("id"))
            return await service.can_send_reminder(phone_number, reminder_type, min_interval_seconds)
        except Exception as e:
            self.logger.error(f"Error checking can_send_reminder: {str(e)}")
            return False

    async def record_reminder_sent(self, phone_number: str, reminder_type: str) -> None:
        """
        Записывает информацию об отправленном напоминании

        Args:
            phone_number: Номер телефона пользователя
            reminder_type: Тип напоминания
        """
        try:
            # Пытаемся получить пользователя по номеру телефона
            user = await self.user_repository.get_by_phone(phone_number)

            if not user:
                return

            # Используем предпочитаемый сервис пользователя
            service = await self.get_preferred_service(user.get("id"))
            await service.record_reminder_sent(phone_number, reminder_type)
        except Exception as e:
            self.logger.error(f"Error recording reminder sent: {str(e)}")
