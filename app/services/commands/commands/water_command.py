# app/services/commands/commands/water_command.py
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import pytz

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.commands.base_command import BaseCommand
from config import settings


class WaterCommand(BaseCommand):
    """
    Команда для записи потребления воды
    """

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды записи потребления воды

        Args:
            user_id: ID пользователя
            params: Параметры команды (содержит текст сообщения)

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        # Получаем язык пользователя
        lang = None
        if hasattr(self, 'localization_service') and self.localization_service:
            lang = await self.localization_service.get_user_language(user_id)

        self.logger.info(f"Processing water tracking command: params: {params}")

        if not params or 'params' not in params:
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Water.INVALID_FORMAT, lang)
            }

        try:
            glasses = float(params['params'][0].lower().strip().replace(',', '.'))

            # Проверка диапазона потребления воды
            if glasses < 0 or glasses >= 20:
                self.logger.error(f"Error recording water tracking: WATER_OUT_OF_RANGE '{glasses}'")
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Water.OUT_OF_RANGE, lang)
                }

            # Конвертируем стаканы в миллилитры (примерно 250 мл в стакане)
            ml_amount = glasses * 250

            # Записываем потребление воды
            result = await self.tracking_service.record_water_intake(user_id, ml_amount)

            if not result:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Water.ERROR, lang)
                }

            # Получаем текущий статус трекинга
            daily_status = await self.tracking_service.get_daily_status(user_id)

            # Получаем данные о потреблении воды за неделю
            end_date = datetime.now(pytz.timezone(settings.TIMEZONE)).date()
            start_date = end_date - timedelta(days=7)
            weekly_water = await self.tracking_service.get_water_history(user_id, start_date, end_date)

            # Расчет средней нормы потребления воды за неделю
            weekly_avg = 0
            days_tracked = 0

            if weekly_water:
                total_water = sum(amount for amount in weekly_water.values())
                days_tracked = len(weekly_water)
                if days_tracked > 0:
                    weekly_avg = total_water / days_tracked

            # Получаем форматтер для отображения сообщения
            tracking_formatter = self.dependencies.get('tracking_formatter_service')
            if tracking_formatter:
                message = self.tracking_formatter_service.format_water_recorded_message(
                    glasses,
                    ml_amount,
                    daily_status,
                    lang,
                    weekly_avg=weekly_avg,
                    days_tracked=days_tracked
                )
            else:
                # Если форматтер недоступен, используем простое сообщение
                message = self.get_localized_message(
                    LK.Commands.Water.RECORDED,
                    lang,
                    amount=glasses,
                    ml_amount=ml_amount
                )

            return {
                "success": True,
                "message": message
            }

        except ValueError:
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Water.INVALID_VALUE, lang)
            }
        except Exception as e:
            # Логирование ошибки
            self.logger.error(f"Error recording water intake: {str(e)}")
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Water.ERROR, lang)
            }

    def get_error_message(self, lang: str) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Commands.Water.INVALID_FORMAT, lang)
