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
            # Проверяем наличие параметров
            if not params or 'params' not in params:
                return {
                    "success": False, 
                    "message": self.messages.INVALID_COMPLIANCE_FORMAT
                }
            
            # Распаковываем параметры
            compliance_match = re.match(
                r'^(выполнено|частично|заменил|пропустил)\s+(\w+)$', 
                params['params'][0].lower()
            )
            
            if not compliance_match:
                return {
                    "success": False, 
                    "message": self.messages.INVALID_COMPLIANCE_FORMAT
                }
            
            # Извлекаем статус и тип приема пищи
            status_text, meal_type_ru = compliance_match.groups()
            
            # Маппинг статусов
            status_map = {
                'выполнено': MealComplianceStatus.FOLLOWED,
                'частично': MealComplianceStatus.PARTIALLY,
                'заменил': MealComplianceStatus.SUBSTITUTED,
                'пропустил': MealComplianceStatus.SKIPPED
            }
            
            # Проверяем корректность статуса
            if status_text not in status_map:
                return {
                    "success": False, 
                    "message": self.messages.INVALID_COMPLIANCE_TYPE
                }
            
            # Маппинг типов приема пищи
            meal_type_map = {
                "завтрак": "breakfast",
                "обед": "lunch",
                "ужин": "dinner",
                "перекус": "snack"
            }
            
            # Проверяем корректность типа приема пищи
            if meal_type_ru not in meal_type_map:
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
                print(f"Ошибка при записи соблюдения плана: {str(e)}")
                return {
                    "success": False,
                    "message": self.messages.COMPLIANCE_RECORD_ERROR
                }

        except Exception as e:
            print(f"Ошибка при обработке команды комплаенса: {str(e)}")
            return {
                "success": False,
                "message": "Произошла ошибка при обработке команды. Попробуйте позже."
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.messages.INVALID_COMPLIANCE_FORMAT