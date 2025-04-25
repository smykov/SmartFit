from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ICommand(ABC):
    """
    Интерфейс команды с базовыми методами выполнения
    """
    @abstractmethod
    async def can_execute(self, user_id: str) -> bool:
        """
        Проверка возможности выполнения команды
        
        Args:
            user_id: ID пользователя
        
        Returns:
            bool: Возможность выполнения команды
        """
        pass

    @abstractmethod
    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды
        
        Args:
            user_id: ID пользователя
            params: Дополнительные параметры команды
        
        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        pass

    @abstractmethod
    def get_error_message(self, lang: str) -> str:
        """
        Получение сообщения об ошибке
        
        Returns:
            str: Сообщение об ошибке
            lang: Язык пользователя
        """
        pass