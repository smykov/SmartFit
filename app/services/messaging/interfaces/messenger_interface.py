# app/services/messaging/interfaces/messenger_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IMessenger(ABC):
    """
    Интерфейс для мессенджера, обрабатывающего сообщения для конкретной платформы
    Ответственность: Парсинг и форматирование сообщений
    """

    @abstractmethod
    async def parse_incoming_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Парсит входящее сообщение для конкретной платформы

        Args:
            data: Данные входящего сообщения

        Returns:
            Dict[str, Any]: Стандартизированное представление сообщения
        """
        pass

    @abstractmethod
    def format_outgoing_message(self, message: str) -> str:
        """
        Форматирует исходящее сообщение для конкретной платформы

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
