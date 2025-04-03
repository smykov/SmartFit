from typing import Dict, Any, Optional

from app.services.commands.interfaces.command_interface import ICommand

from app.localization.command_handler_messages import CommandHandlerMessages


class BaseCommand(ICommand):
    """
    Базовый класс для всех команд
    """
    def __init__(self, dependencies: Dict[str, Any]):
        """
        Инициализация базовой команды с зависимостями
        
        Args:
            dependencies: Словарь зависимостей для команды
        """
        self.dependencies = dependencies
        self.messages = CommandHandlerMessages()

    async def can_execute(self, user_id: str) -> bool:
        """
        Базовая проверка возможности выполнения команды
        По умолчанию всегда возвращает True
        
        Args:
            user_id: ID пользователя
        
        Returns:
            bool: Возможность выполнения команды
        """
        return True

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Базовый метод выполнения команды
        
        Args:
            user_id: ID пользователя
            params: Дополнительные параметры команды
        
        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        raise NotImplementedError("Метод execute должен быть реализован в дочернем классе")

    def get_error_message(self) -> str:
        """
        Базовое сообщение об ошибке
        
        Returns:
            str: Сообщение об ошибке
        """
        return self.messages.COMMAND_NOT_FOUND