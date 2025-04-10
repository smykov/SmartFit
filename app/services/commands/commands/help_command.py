from typing import Dict, Any, Optional

from app.services.commands.base_command import BaseCommand


class HelpCommand(BaseCommand):
    """
    Команда для отображения справки
    """

    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды получения справки по командам

        Args:
            user_id: ID пользователя
            params: Параметры команды

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        help_message = self.messages.get_help_message()
        return {
            "success": True,
            "message": help_message
        }