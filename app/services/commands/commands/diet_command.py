# app/services/commands/commands/diet_command.py
import re
from datetime import datetime, timedelta
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
                - day: день недели (today, tomorrow, monday, tuesday, wednesday, thursday, friday, saturday, sunday)
                  или конкретная дата в формате YYYY-MM-DD
                - full: показать полный план (true/false)

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        # Получаем язык пользователя
        lang = None
        if hasattr(self, 'localization_service') and self.localization_service:
            lang = await self.localization_service.get_user_language(user_id)

        try:
            # Получаем текущий план диеты
            diet_plan = await self.diet_service.get_current_diet(user_id)

            # Получаем пользователя из репозитория
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.User.NOT_FOUND, lang)
                }

            phone_number = user.get('phone_number', '')

            if not diet_plan:
                # Запускаем генерацию нового плана диеты
                await self.messenger_service.send_message(
                    phone_number,
                    self.get_localized_message(LK.Commands.Diet.DIET_GENERATION_STARTED, lang),
                    {"user_id": user_id}
                )
                await self.messenger_service.send_message(
                    phone_number,
                    self.get_localized_message(LK.Commands.Diet.DIET_GENERATION_DETAILS, lang),
                    {"user_id": user_id}
                )

                # Запускаем генерацию короткого плана диеты
                diet_plan = await self.diet_service.generate_short_diet_plan(user_id)

                if not diet_plan or "error" in diet_plan:
                    await self.messenger_service.send_template_message(
                        phone_number,
                        LK.Diet.Short.CREATED,
                        user_id)
                    return {
                        "success": False,
                        "message": self.get_localized_message(LK.Diet.Short.CREATING_ERROR, lang)
                    }

            # Обработка плана в статусе "pending" (ожидание согласования)
            if diet_plan.get('version') == "short" and diet_plan.get('status') == "pending":
                # Отправляем сводку плана для согласования
                summary = self.diet_service.get_short_diet_summary(diet_plan, lang)
                await self.messenger_service.send_message(
                    phone_number,
                    summary,
                    {"user_id": user_id}
                )
                # Отправляем информацию о следующих шагах
                next_steps = self.diet_service.get_short_diet_next_steps(lang)
                await self.messenger_service.send_message(
                    phone_number,
                    next_steps,
                    {"user_id": user_id}
                )
                # Отправляем информацию о согласовании
                await self.messenger_service.send_template_message(
                    phone_number,
                    LK.Diet.Short.CONFORMATION,
                    user_id)

                return {
                    "success": True,
                    "action": "short_diet_generated",
                    "message": self.get_localized_message(LK.Diet.Short.CREATED, lang)
                }

            # Обработка параметров
            # Получаем текущую дату и время
            current_datetime = datetime.now(pytz.timezone(settings.TIMEZONE))
            target_date = current_datetime.date()

            # Обработка параметра day
            if params and "day" in params:
                day_param = params["day"].lower() if isinstance(params["day"], str) else "today"

                # Проверяем, является ли параметр day датой в формате YYYY-MM-DD
                date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')

                if date_pattern.match(day_param):
                    try:
                        # Преобразуем строку в дату
                        target_date = datetime.strptime(day_param, "%Y-%m-%d").date()
                    except ValueError:
                        self.logger.warning(f"Некорректный формат даты: {day_param}")
                        # В случае ошибки используем текущую дату
                        target_date = current_datetime.date()
                elif day_param == "today":
                    target_date = current_datetime.date()
                elif day_param == "tomorrow":
                    target_date = (current_datetime + timedelta(days=1)).date()
                elif day_param in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    # Определяем день недели в виде числа (0 - понедельник, 6 - воскресенье)
                    weekday_map = {
                        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                        "friday": 4, "saturday": 5, "sunday": 6
                    }
                    target_weekday = weekday_map[day_param]
                    current_weekday = current_datetime.weekday()

                    # Если запрошенный день недели уже прошел на этой неделе, берем следующую неделю
                    days_ahead = target_weekday - current_weekday
                    if days_ahead <= 0:  # Если это текущий день или прошедший день недели
                        days_ahead += 7

                    target_date = (current_datetime + timedelta(days=days_ahead)).date()

            # Обработка параметра full
            show_full_plan = False
            if params and "full" in params:
                if isinstance(params["full"], bool):
                    show_full_plan = params["full"]
                elif isinstance(params["full"], str):
                    show_full_plan = params["full"].lower() in ["true", "yes", "1"]

            # Если запрошен полный план
            if show_full_plan:
                # Проверяем, имеет ли план статус "active"
                if diet_plan.get('version') == "full" and diet_plan.get('status') == "active":
                    # Форматируем и отправляем полный план диеты
                    formatted_plan_messages = self.diet_service.get_full_diet_plan(diet_plan, lang)

                    return {
                        "success": True,
                        "messages": formatted_plan_messages
                    }
                else:
                    return {
                        "success": False,
                        "message": self.get_localized_message(LK.Diet.Full.NO_PLAN, lang)
                    }
            else:
                # Получаем план на конкретный день
                day_plan = await self.diet_service.get_diet_for_day(user_id, target_date)

                if not day_plan:
                    # Если плана на этот день нет, сообщаем об этом
                    date_format = self.get_localized_message(LK.Common.DAY_FORMAT, lang)
                    formatted_date = target_date.strftime(date_format)

                    day_name = target_date.strftime("%A").lower()
                    day_localized = self.get_localized_message(
                        LK.Common.WEEKDAY_NAMES.format(day_name),
                        lang
                    )

                    return {
                        "success": False,
                        "message": self.get_localized_message(
                            LK.Commands.Diet.NO_DIET_FOR_TODAY,
                            lang,
                            day=day_localized,
                            date=formatted_date
                        )
                    }

                # Форматируем и отправляем план на конкретный день
                formatted_plan_messages = self.diet_service.get_day_diet_plan(diet_plan, target_date, lang)
                # tracking_info_message = self.diet_service.get_diet_tracking_info_message(lang)

                # TODO добавить список продуктов\покупок на день + обработка запросов на отметку что есть из списка

                return {
                    "success": True,
                    "messages": [*formatted_plan_messages]
                }

        except Exception as e:
            self.logger.error(f"Error processing diet command: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Diet.ERROR, lang)
            }

    def get_error_message(self, lang) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Commands.Diet.NO_DIET_PLAN, lang)
