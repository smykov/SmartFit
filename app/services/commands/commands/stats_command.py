# app/services/commands/commands/stats_command.py
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import pytz

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.commands.base_command import BaseCommand
from config import settings


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
        # Получаем язык пользователя
        lang = None
        if hasattr(self, 'localization_service') and self.localization_service:
            lang = await self.localization_service.get_user_language(user_id)
        try:
            # Получаем прогресс по весу
            weight_progress = await self.tracking_service.calculate_weight_progress(user_id)

            # Получаем статус трекинга на сегодня
            today_status = await self.tracking_service.get_daily_status(user_id)

            # Получаем данные о соблюдении плана за последние 7 дней
            end_date = today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()
            start_date = end_date - timedelta(days=7)
            weekly_compliance = await self.tracking_service.get_compliance_by_period(user_id, start_date, end_date)
            today_compliance_list = await self.tracking_service.get_compliance_by_period(user_id, today, today)
            today_compliance = None

            if today_compliance_list and len(today_compliance_list) >= 1:
                today_compliance = today_compliance_list[0]

            # Получаем данные о соблюдении плана на сегодня
            # TODO добавить возможность указать период статистики в команде и обрабатывать день/неделю/месяц или конкретный день, неделю, месяц
            # today_compliance = await self.tracking_service.get_diet_compliance(user_id)

            # Форматируем статистику через форматтер
            # TODO поменять заголовок что статистика за день, общее соблюдение плана не верно считается - проверить
            stats_message = self.tracking_formatter_service.format_stats_message(
                weight_progress,
                today_status,
                today_compliance,
                lang
            )

            # Добавляем отчет о соблюдении плана за неделю
            # TODO в недельный отчет добавить подтребление воды и прогресс по весу. Убрать пустые дни с начала периода отслеживания или учитывать дату когда план питиния был создан и считать с этой даты, тк при первых днях статистика будет пустая хотя пользователь только начал пользоваться, возможно добавить сюда среднию в день.
            date_range = self.get_localized_message(LK.Tracking.Stats.LAST_WEEK, lang)
            compliance_report = self.tracking_formatter_service.format_compliance_report(
                date_range,
                weekly_compliance,
                lang
            )

            return {
                "success": True,
                "messages": [stats_message, compliance_report]
            }

        except Exception as e:
            # Логирование ошибки
            self.logger.error(f"Error getting statistics: {str(e)}")
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Stats.ERROR, lang)
            }

    def get_error_message(self, lang) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Commands.Stats.ERROR, lang)
