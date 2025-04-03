from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ICommandHandler(ABC):
    """
    Интерфейс для обработчика команд
    """
    @abstractmethod
    async def handle_command(
        self, 
        user: Dict[str, Any], 
        command_type: str, 
        command_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Обработка команды пользователя
        
        Args:
            user: Данные пользователя
            command_type: Тип команды
            command_params: Параметры команды
        
        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        pass

    @abstractmethod
    def get_help_message(self) -> str:
        """
        Получение справочного сообщения со списком команд
        
        Returns:
            str: Справочное сообщение
        """
        pass