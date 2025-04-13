# app/services/commands/commands/help_command.py
from typing import Dict, Any, Optional

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.commands.base_command import BaseCommand


class HelpCommand(BaseCommand):
    """
    Команда для отображения справки
    """

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды получения справки по командам

        Args:
            user_id: ID пользователя
            params: Параметры команды

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        # Получаем язык пользователя, если доступен сервис локализации
        lang = None
        if hasattr(self, 'localization_service') and self.localization_service:
            lang = await self.localization_service.get_user_language(user_id)

        # Получаем локализованное сообщение справки
        help_message = self.get_localized_message(LK.Common.HELP_COMMANDS_LIST, lang)

        return {
            "success": True,
            "message": help_message
        }