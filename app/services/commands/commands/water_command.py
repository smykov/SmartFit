import re
from typing import Dict, Any, Optional

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
        self.logger.info(f"Обработка команды трекинга воды: params: {params}")

        if not params or 'params' not in params:
            return {
                "success": False,
                "message": self.messages.INVALID_WATER_FORMAT
            }

        try:
            amount = float(params['params'][0].lower().strip().replace(',', '.'))

            # Проверка диапазона потребления воды
            if amount < 0 or amount >= 20:
                self.logger.error(f"Ошибка при записи трекинга воды: WATER_OUT_OF_RANGE '{amount}'")
                return {
                    "success": False,
                    "message": self.messages.WATER_OUT_OF_RANGE
                }

            # Конвертируем стаканы в миллилитры (примерно 250 мл в стакане)
            ml_amount = amount * 250

            # Запись потребления воды через типизированный сервис трекинга
            await self.tracking_service.record_water_intake(user_id, ml_amount)

            # Получаем статус трекинга
            status = await self.tracking_service.get_daily_status(user_id)

            # Форматируем сообщение о записи воды
            message = self.messages.format_water_recorded_message(amount, ml_amount, status)

            return {
                "success": True,
                "message": message
            }

        except ValueError:
            return {
                "success": False,
                "message": self.messages.INVALID_WATER_VALUE
            }
        except Exception as e:
            # Логирование ошибки
            self.logger.error(f"Ошибка при записи потребления воды: {str(e)}")
            return {
                "success": False,
                "message": "Произошла ошибка при записи потребления воды. Попробуйте позже."
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.messages.INVALID_WATER_FORMAT
