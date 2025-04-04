import re
from typing import Dict, Any, Optional
from datetime import datetime
import pytz
from app.services.commands.base_command import BaseCommand
from app.models.tracking import MealComplianceStatus
from config import settings


class ComplianceCommand(BaseCommand):
    """
    Команда для отметки о соблюдении плана питания
    """

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды отметки о соблюдении

        Args:
            user_id: ID пользователя
            params: Параметры команды (содержит текст сообщения)

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        try:
            self.logger.info(f"Обработка команды соблюдения: params: {params}")

            # Проверяем наличие параметров
            if not params or 'params' not in params:
                self.logger.error(f"Ошибка при записи соблюдения плана")
                return {
                    "success": False,
                    "message": self.messages.INVALID_COMPLIANCE_FORMAT
                }

            # Получаем текст сообщения и выполняем предварительную очистку
            status_text = params['params'][0].lower().strip()
            meal_type_ru = params['params'][1].lower().strip()

            # Маппинг статусов
            status_map = {
                'выполнено': MealComplianceStatus.FOLLOWED,
                'частично': MealComplianceStatus.PARTIALLY,
                'заменил': MealComplianceStatus.SUBSTITUTED,
                'заменила': MealComplianceStatus.SUBSTITUTED,
                'пропустил': MealComplianceStatus.SKIPPED,
                'пропустила': MealComplianceStatus.SKIPPED
            }

            # Проверяем корректность статуса
            if status_text not in status_map:
                self.logger.error(f"Ошибка при записи соблюдения плана: Неизвестный тип соблюдения плана '{status_text}'")

                return {
                    "success": False,
                    "message": self.messages.INVALID_COMPLIANCE_TYPE
                }

            # Маппинг типов приема пищи с учетом разных форм слов
            meal_type_map = {
                "завтрак": "breakfast",
                "обед": "lunch",
                "ужин": "dinner",
                "перекус": "snack"
            }

            # Проверяем корректность типа приема пищи
            if meal_type_ru not in meal_type_map:
                self.logger.error(f"Ошибка при записи соблюдения плана: Неизвестный тип приема пищи '{meal_type_ru}'")
                return {
                    "success": False,
                    "message": self.messages.INVALID_MEAL_TYPE
                }

            # Получаем текущую дату
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Проверяем наличие плана диеты
            diet_plan = await self.dependencies['diet_service'].get_current_diet(user_id)

            if not diet_plan:
                return {
                    "success": False,
                    "message": self.messages.NO_DIET_PLAN_FOR_COMPLIANCE
                }

            # Преобразуем русское название в английское
            meal_type = meal_type_map[meal_type_ru]
            status = status_map[status_text]

            self.logger.info(f"Запись соблюдения плана: тип={meal_type}, статус={status}")

            try:
                # Записываем соблюдение через трекинг-сервис
                result = await self.dependencies['tracking_service'].record_meal_compliance(
                    user_id,
                    today,
                    meal_type,
                    status,
                    None,  # notes
                    None  # alternative_meal
                )

                if not result:
                    return {
                        "success": False,
                        "message": self.messages.COMPLIANCE_RECORD_ERROR
                    }

                # Получаем данные о соблюдении плана
                compliance_data = await self.dependencies['tracking_service'].get_diet_compliance(user_id, today)

                # Форматируем сообщение о соблюдении
                message = self.messages.format_compliance_message(
                    meal_type_ru,
                    status,
                    compliance_data
                )

                return {
                    "success": True,
                    "message": message
                }

            except Exception as e:
                self.logger.error(f"Ошибка при записи соблюдения плана: {str(e)}")
                return {
                    "success": False,
                    "message": self.messages.COMPLIANCE_RECORD_ERROR
                }

        except Exception as e:
            self.logger.error(f"Ошибка при обработке команды комплаенса: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": self.messages.COMPLIANCE_RECORD_ERROR
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.messages.INVALID_COMPLIANCE_FORMAT
