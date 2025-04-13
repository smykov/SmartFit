# app/services/commands/commands/stats_command.py
from typing import Dict, Any, Optional

from app.constants.localization_keys import LocalizationKeys as LK
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
            # Получаем язык пользователя
            lang = None
            if hasattr(self, 'localization_service') and self.localization_service:
                lang = await self.localization_service.get_user_language(user_id)

            # Получаем прогресс по весу
            weight_progress = await self.dependencies['tracking_service'].calculate_weight_progress(user_id)

            # Получаем статус трекинга на сегодня
            today_status = await self.dependencies['tracking_service'].get_daily_status(user_id)

            # Получаем данные о соблюдении плана на сегодня
            today_compliance = await self.dependencies['tracking_service'].get_diet_compliance(user_id)

            # Форматируем статистику через форматтер, если он доступен
            tracking_formatter = self.dependencies.get('tracking_formatter_service')
            if tracking_formatter:
                stats_message = tracking_formatter.format_stats_message(
                    weight_progress,
                    today_status,
                    today_compliance,
                    lang
                )
            else:
                # Если форматтер недоступен, используем простое сообщение
                stats_message = self.get_localized_message(
                    "tracking.stats_default_message",
                    lang
                )

            return {
                "success": True,
                "message": stats_message
            }

        except Exception as e:
            # Логирование ошибки
            self.logger.error(f"Error getting statistics: {str(e)}")
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Stats.ERROR, lang)
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Commands.Stats.ERROR)
