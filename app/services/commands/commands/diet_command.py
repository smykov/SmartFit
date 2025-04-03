from datetime import datetime
from typing import Dict, Any, Optional

import pytz

from app.services.commands.base_command import BaseCommand
from config import settings


class DietCommand(BaseCommand):
    """
    Команда для работы с планом диеты
    """
    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды работы с диетой
        
        Args:
            user_id: ID пользователя
            params: Параметры команды
        
        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        try:
            # Получаем текущий план диеты
            diet_plan = await self.dependencies['diet_service'].get_current_diet(user_id)

            if not diet_plan:
                # Запускаем генерацию нового плана диеты
                await self.dependencies['message_service'].send_message(
                    self.dependencies['user']['phone_number'], 
                    self.messages.DIET_GENERATION_STARTED
                )
                await self.dependencies['message_service'].send_message(
                    self.dependencies['user']['phone_number'], 
                    self.messages.DIET_GENERATION_DETAILS
                )

                # Запускаем генерацию короткого плана диеты
                short_plan = await self.dependencies['diet_service'].generate_short_diet_plan(user_id)

                if short_plan and "error" not in short_plan:
                    # Отправляем сводку плана для согласования
                    summary = self.dependencies['diet_service'].get_short_diet_summary(short_plan)
                    await self.dependencies['message_service'].send_message(
                        self.dependencies['user']['phone_number'], 
                        summary
                    )

                    return {
                        "success": True, 
                        "action": "short_diet_generated",
                        "message": "План диеты создан и отправлен для согласования"
                    }
                else:
                    await self.dependencies['message_service'].send_message(
                        self.dependencies['user']['phone_number'], 
                        self.messages.NO_DIET_PLAN
                    )
                    return {
                        "success": False, 
                        "message": self.messages.NO_DIET_PLAN
                    }

            # Получаем текущую дату
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Получаем план на сегодня
            today_plan = await self.dependencies['diet_service'].get_diet_for_day(user_id, today)

            if not today_plan:
                return {
                    "success": False, 
                    "message": self.messages.NO_DIET_FOR_TODAY
                }

            # Форматируем и отправляем план на сегодня
            formatted_plan = self.dependencies['diet_service'].get_day_diet_plan(diet_plan, today)
            
            return {
                "success": True, 
                "message": formatted_plan
            }

        except Exception as e:
            print(f"Ошибка при работе с диетой: {str(e)}")
            return {
                "success": False, 
                "message": "Произошла ошибка при работе с планом диеты. Попробуйте позже."
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке
        
        Returns:
            str: Сообщение об ошибке
        """
        return self.messages.NO_DIET_PLAN