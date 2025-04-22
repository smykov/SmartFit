# app/services/messaging/messengers/base_messenger.py
import logging
from typing import Dict, Any, Optional, List
from abc import abstractmethod

from app.services.messaging.interfaces.messenger_interface import IMessenger
from app.services.localization.localization_interface import ILocalizationService
from app.db.interfaces.message_repository_interface import IMessageRepository


class BaseMessenger(IMessenger):
    """
    Базовый класс для реализации мессенджеров
    """

    def __init__(self,
                 message_repository: IMessageRepository,
                 localization_service: ILocalizationService):
        self.message_repository = message_repository
        self.localization_service = localization_service
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_localized_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        """Получение локализованного сообщения"""
        if self.localization_service:
            return self.localization_service.get_message(key, lang, **params)
        return key

    @abstractmethod
    async def initialize(self) -> bool:
        """Инициализация мессенджера"""
        pass

    @abstractmethod
    async def send_message(self, recipient_id: str, message: str,
                           context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Отправка сообщения"""
        pass

    @abstractmethod
    async def send_template_message(self, recipient_id: str, template_name: str,
                                    user_id: Optional[str] = None,
                                    params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Отправка шаблонного сообщения"""
        pass

    @abstractmethod
    def get_messenger_type(self) -> str:
        """Получение типа мессенджера"""
        pass

    @abstractmethod
    def parse_incoming_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Парсинг входящего сообщения"""
        pass

    def format_outgoing_message(self, message: str) -> str:
        """
        Базовая реализация форматирования сообщения
        Переопределяется в конкретных мессенджерах
        """
        return message