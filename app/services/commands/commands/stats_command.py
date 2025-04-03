from typing import Dict, Any, Optional
from app.services.commands.base_command import BaseCommand

class StatsCommand(BaseCommand):
    """
    Команда для получения статистики прогресса
    """
    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды получения статистики
        
        Args:
            user_id: ID пользователя
            params: Параметры команды
        
        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        try:
            # Получаем прогресс по весу
            weight_progress = await self.dependencies['tracking_service'].calculate_weight_progress(user_id)

            # Получаем статус трекинга на сегодня
            today_status = await self.dependencies['tracking_service'].get_daily_status(user_id)

            # Получаем данные о соблюдении плана на сегодня
            today = await self.dependencies['tracking_service'].get_diet_compliance(user_id)

            # Форматируем статистику
            stats_message = self.messages.format_stats_message(
                weight_progress, 
                today_status, 
                today
            )

            return {
                "success": True, 
                "message": stats_message
            }

        except Exception as e:
            print(f"Ошибка при получении статистики: {str(e)}")
            return {
                "success": False, 
                "message": self.messages.STATS_ERROR
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке
        
        Returns:
            str: Сообщение об ошибке
        """
        return self.messages.STATS_ERROR