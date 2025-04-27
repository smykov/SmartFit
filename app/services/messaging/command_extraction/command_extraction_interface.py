# app/services/messaging/command_extraction/command_extraction_interface.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class ICommandExtractor(ABC):
    """Интерфейс для экстракторов команд из текстовых сообщений"""

    @abstractmethod
    async def extract_commands(self, message: str, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Извлекает команды из текстового сообщения пользователя

        Args:
            message: Текст сообщения
            user_id: ID пользователя
            context: Контекст пользователя и разговора

        Returns:
            Dict[str, Any]: Результат извлечения с командами и ответом
        """
        pass