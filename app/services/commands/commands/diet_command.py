# app/services/commands/commands/diet_command.py
from datetime import datetime
from typing import Dict, Any, Optional

import pytz

from app.constants.localization_keys import LocalizationKeys as LK
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
            # Получаем язык пользователя
            lang = None
            if hasattr(self, 'localization_service') and self.localization_service:
                lang = await self.localization_service.get_user_language(user_id)

            # Получаем текущий план диеты
            diet_plan = await self.dependencies['diet_service'].get_current_diet(user_id)

            phone_number = self.dependencies['user'].get('phone_number', '')

            if not diet_plan:
                # Запускаем генерацию нового плана диеты
                await self.dependencies['message_service'].send_message(
                    phone_number,
                    self.get_localized_message(LK.Commands.Diet.DIET_GENERATION_STARTED, lang)
                )
                await self.dependencies['message_service'].send_message(
                    phone_number,
                    self.get_localized_message(LK.Commands.Diet.DIET_GENERATION_DETAILS, lang)
                )

                # Запускаем генерацию короткого плана диеты
                diet_plan = await self.dependencies['diet_service'].generate_short_diet_plan(user_id)

                if not diet_plan or "error" in diet_plan:
                    await self.dependencies['message_service'].send_template_message(
                        phone_number,
                        LK.Diet.Short.CREATED,
                        user_id)
                    return {
                        "success": False,
                        "message": self.get_localized_message(LK.Diet.Short.CREATING_ERROR, lang)
                    }

            if diet_plan.get('version') == "short" and diet_plan.get('status') == "pending":
                # Отправляем сводку плана для согласования
                summary = await self.dependencies['diet_service'].get_short_diet_summary(diet_plan, lang)
                await self.dependencies['message_service'].send_message(
                    phone_number,
                    summary
                )
                # Отправляем информация о следующих шагах
                next_steps = self.dependencies['diet_service'].get_short_diet_next_steps(lang)
                await self.dependencies['message_service'].send_message(
                    phone_number,
                    next_steps
                )
                # Отправляем информация о согласовании
                await self.dependencies['message_service'].send_template_message(
                    phone_number,
                    LK.Diet.Short.CONFORMATION,
                    user_id)

                return {
                    "success": True,
                    "action": "short_diet_generated",
                    "message": self.get_localized_message(LK.Diet.Short.CREATED, lang)
                }

            # Получаем текущую дату
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Получаем план на сегодня
            today_plan = await self.dependencies['diet_service'].get_diet_for_day(user_id, today)

            if not today_plan:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Diet.NO_DIET_FOR_TODAY, lang)
                }
            # Форматируем и отправляем план на сегодня
            formatted_plan_messages = self.dependencies['diet_service'].get_day_diet_plan(diet_plan, today, lang)
            tracking_info_message = self.dependencies['diet_service'].get_diet_tracking_info_message(lang)

            # TODO добавить список продуктов\покупок на день + обработка запросов на отметку что есть из списка

            return {
                "success": True,
                "messages": [*formatted_plan_messages, tracking_info_message]
            }

        except Exception as e:
            self.logger.error(f"Error processing diet command: {str(e)}")
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Diet.ERROR, lang)
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Commands.Diet.NO_DIET_PLAN)
