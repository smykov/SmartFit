# app/services/messaging/messengers/messenger_base.py
import logging
from abc import abstractmethod
from typing import Dict, Any, Optional

from app.services.localization.localization_interface import ILocalizationService
from app.services.messaging.interfaces.messenger_interface import IMessenger


class MessengerBase(IMessenger):
    """
    Базовый класс для мессенджеров
    Ответственность: Предоставление общей функциональности для всех мессенджеров
    """

    def __init__(self, localization_service: ILocalizationService):
        """
        Инициализация базового мессенджера

        Args:
            localization_service: Сервис локализации
        """
        self.localization_service = localization_service
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_localized_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        """
        Получение локализованного сообщения

        Args:
            key: Ключ сообщения
            lang: Язык сообщения
            **params: Параметры для форматирования

        Returns:
            str: Локализованное сообщение
        """
        if self.localization_service:
            return self.localization_service.get_message(key, lang, **params)
        return key

    @abstractmethod
    async def parse_incoming_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Парсит входящее сообщение

        Args:
            data: Данные входящего сообщения

        Returns:
            Dict[str, Any]: Стандартизированное представление сообщения
        """
        pass

    @abstractmethod
    def format_outgoing_message(self, message: str) -> str:
        """
        Форматирует исходящее сообщение

        Args:
            message: Исходный текст сообщения

        Returns:
            str: Отформатированное сообщение
        """
        pass

    @abstractmethod
    def get_messenger_type(self) -> str:
        """
        Возвращает тип мессенджера

        Returns:
            str: Тип мессенджера (например, "whatsapp", "telegram")
        """
        pass
