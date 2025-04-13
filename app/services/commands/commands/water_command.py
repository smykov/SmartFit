# app/services/commands/commands/water_command.py
import re
from typing import Dict, Any, Optional

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.commands.base_command import BaseCommand


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
            amount = float(params['params'][0].lower().strip().replace(',', '.'))

            # Проверка диапазона потребления воды
            if amount < 0 or amount >= 20:
                self.logger.error(f"Error recording water tracking: WATER_OUT_OF_RANGE '{amount}'")
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Water.OUT_OF_RANGE, lang)
                }

            # Конвертируем стаканы в миллилитры (примерно 250 мл в стакане)
            ml_amount = amount * 250

            # Запись потребления воды через типизированный сервис трекинга
            await self.tracking_service.record_water_intake(user_id, ml_amount)

            # Получаем статус трекинга
            status = await self.tracking_service.get_daily_status(user_id)

            # Получаем форматтер для отображения сообщения
            tracking_formatter = self.dependencies.get('tracking_formatter_service')
            if tracking_formatter:
                message = tracking_formatter.format_water_recorded_message(
                    amount,
                    ml_amount,
                    status,
                    lang
                )
            else:
                # Если форматтер недоступен, используем простое сообщение
                message = self.get_localized_message(
                    LK.Commands.Water.RECORDED,
                    lang,
                    amount=amount,
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

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Commands.Water.INVALID_FORMAT)