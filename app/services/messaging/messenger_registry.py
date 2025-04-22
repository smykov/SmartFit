# app/services/messaging/messenger_registry.py
from typing import Dict, Any, Optional, Type
import logging

from app.services.messaging.interfaces.messenger_interface import IMessenger

logger = logging.getLogger(__name__)


class MessengerRegistry:
    """
    Реестр для управления зарегистрированными мессенджерами
    """

    def __init__(self):
        """Инициализация реестра"""
        self._messengers: Dict[str, IMessenger] = {}
        self._messenger_classes: Dict[str, Type[IMessenger]] = {}
        logger.info("MessengerRegistry initialized")

    def register_messenger_class(self, messenger_type: str, messenger_class: Type[IMessenger]) -> None:
        """Регистрация класса мессенджера"""
        self._messenger_classes[messenger_type] = messenger_class
        logger.info(f"Messenger class '{messenger_type}' registered")

    def register_messenger_instance(self, messenger_type: str, messenger: IMessenger) -> None:
        """
        Регистрация экземпляра мессенджера

        Args:
            messenger_type: Тип мессенджера (whatsapp, telegram и т.д.)
            messenger: Экземпляр класса мессенджера
        """
        self._messengers[messenger_type] = messenger
        logger.info(f"Messenger instance '{messenger_type}' registered")

    def get_messenger(self, messenger_type: str) -> Optional[IMessenger]:
        """
        Получение экземпляра мессенджера по типу

        Args:
            messenger_type: Тип мессенджера

        Returns:
            Optional[IMessenger]: Экземпляр мессенджера или None
        """
        messenger = self._messengers.get(messenger_type)
        if not messenger:
            logger.warning(f"Messenger '{messenger_type}' not found in registry")
        return messenger

    def get_all_messengers(self) -> Dict[str, IMessenger]:
        """
        Получение всех зарегистрированных мессенджеров

        Returns:
            Dict[str, IMessenger]: Словарь мессенджеров
        """
        return self._messengers.copy()

    def has_messenger(self, messenger_type: str) -> bool:
        """
        Проверяет, зарегистрирован ли указанный мессенджер

        Args:
            messenger_type: Тип мессенджера

        Returns:
            bool: True, если мессенджер зарегистрирован
        """
        return messenger_type in self._messengers