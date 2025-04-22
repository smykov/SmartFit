# app/services/messaging/interfaces/messenger_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IMessenger(ABC):
    """
    Универсальный интерфейс для всех мессенджеров
    """

    @abstractmethod
    async def initialize(self) -> bool:
        """Инициализация сервиса мессенджера"""
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

    @abstractmethod
    def format_outgoing_message(self, message: str) -> str:
        """Форматирование исходящего сообщения"""
        pass