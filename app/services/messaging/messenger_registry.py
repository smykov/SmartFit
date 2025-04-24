# app/services/messaging/messenger_registry.py
from typing import Dict, Any, Optional
import logging

from app.services.messaging.interfaces.messenger_interface import IMessenger

logger = logging.getLogger(__name__)


class MessengerRegistry:
    """
    Реестр для управления зарегистрированными мессенджерами
    Ответственность: Регистрация и получение мессенджеров по их типу
    """

    def __init__(self):
        """Инициализация реестра"""
        self._messengers: Dict[str, IMessenger] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("MessengerRegistry initialized")

    def register_messenger(self, messenger: IMessenger) -> None:
        """
        Регистрация экземпляра мессенджера

        Args:
            messenger: Экземпляр мессенджера
        """
        messenger_type = messenger.get_messenger_type()
        self._messengers[messenger_type] = messenger
        self.logger.info(f"Messenger '{messenger_type}' registered")

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
            self.logger.warning(f"Messenger '{messenger_type}' not found in registry")
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
