# app/services/commands/commands/diet_update_command.py
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Type

import pytz

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.commands.base_command import BaseCommand
from app.services.commands.commands.diet_command import DietCommand
from app.utils.date_helper import DateHelper
from config import settings


class DietUpdateCommandBase(BaseCommand):
    """
    Базовая команда для обновления плана диеты, содержащая общую логику
    """

    async def can_execute(self, user_id: str) -> bool:
        """
        Проверяет возможность выполнения команды обновления плана диеты

        Args:
            user_id: ID пользователя

        Returns:
            bool: Возможность выполнения команды
        """
        try:
            # Проверяем наличие активного плана
            diet_plan = await self.diet_service.get_current_diet(user_id)
            return diet_plan is not None
        except Exception as e:
            self.logger.error(f"Error checking diet update prerequisites: {str(e)}")
            return False

    @staticmethod
    def create_command(dependencies: Dict[str, Any], user_id: str) -> 'DietUpdateCommandBase':
        """
        Фабричный метод для создания нужного типа команды обновления диеты
        в зависимости от версии текущего плана

        Args:
            dependencies: Словарь зависимостей
            user_id: ID пользователя

        Returns:
            DietUpdateCommandBase: Конкретная команда обновления диеты
        """
        # Создаем временный экземпляр для доступа к сервисам
        temp_command = DietUpdateCommandBase(dependencies)

        try:
            # Получаем текущий план диеты
            diet_plan = asyncio.run(temp_command.diet_service.get_current_diet(user_id))

            # Выбираем тип команды в зависимости от версии плана
            if diet_plan and diet_plan.get("version") == "short" and diet_plan.get("status") == "pending":
                return ShortDietUpdateCommand(dependencies)
            else:
                return FullDietUpdateCommand(dependencies)
        except Exception as e:
            temp_command.logger.error(f"Error creating diet update command: {str(e)}")
            # По умолчанию используем полную версию
            return FullDietUpdateCommand(dependencies)


class ShortDietUpdateCommand(DietUpdateCommandBase):
    """
    Команда для обновления краткой версии плана диеты
    """

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды обновления краткого плана диеты

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

        try:
            # Получаем текущий план диеты
            diet_plan = await self.diet_service.get_current_diet(user_id)
            if not diet_plan:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Diet.Short.NO_PLAN, lang)
                }

            # Получаем данные о пользователе
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.User.NOT_FOUND, lang)
                }

            # Извлекаем параметры
            update_request = None
            original_ai_recommendation = None

            # Получаем текст запроса из параметров
            if not params or "update_request" not in params:
                # Пытаемся получить текст из других возможных мест в параметрах
                update_request = None
                if "params" in params:
                    if isinstance(params["params"], tuple) and len(params["params"]) > 0:
                        update_request = params["params"][0]
                    elif isinstance(params["params"], dict) and "update_request" in params["params"]:
                        update_request = params["params"]["update_request"]

                if not update_request:
                    self.logger.error("Update request text not found in parameters")
                    return {
                        "success": False,
                        "message": self.get_localized_message(LK.Diet.Update.INVALID_FORMAT, lang)
                    }
            else:
                update_request = params["update_request"]

            # Сообщаем пользователю, что обновляем план
            recipient_id = user.get("phone_number", "")
            await self.messenger_service.send_message(
                recipient_id,
                self.get_localized_message(LK.Diet.Short.UPDATING, lang),
                {"user_id": user_id}
            )
            await asyncio.sleep(1)  # Небольшая задержка для последовательности сообщений

            # Обновляем краткий план диеты
            result = await self.diet_service.update_short_diet_plan_by_request(
                diet_plan["id"],
                update_request
            )

            if "error" in result:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Diet.Short.UPDATE_FAILED, lang)
                }

            # Формируем и отправляем сообщение о результате обновления
            if "success" in result and result["success"]:
                # Используем форматтер для получения сообщения об успешном обновлении
                from app.services.formatter.diet_update_formatter import DietUpdateFormatter
                formatter = DietUpdateFormatter(self.localization_service)

                updated_days_keys = list(result.get("updated_days", {}).keys())
                comment = result.get("comment", self.get_localized_message(LK.Diet.Update.DEFAULT_COMMENT, lang))

                update_message = formatter.format_update_success_message(
                    comment,
                    updated_days_keys,
                    lang
                )

                return {
                    "success": True,
                    "message": update_message,
                    "updated_days": updated_days_keys
                }
            else:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Diet.Short.UPDATE_FAILED, lang)
                }

        except Exception as e:
            self.logger.error(f"Error executing short diet update command: {str(e)}")
            return {
                "success": False,
                "message": self.get_localized_message(LK.Diet.Short.UPDATE_FAILED, lang)
            }

    def get_error_message(self, lang: str = None) -> str:
        """
        Получение сообщения об ошибке

        Args:
            lang: Язык пользователя

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Diet.Short.NO_PLAN, lang)


class FullDietUpdateCommand(DietUpdateCommandBase):
    """
    Команда для обновления полной версии плана диеты
    """

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды обновления полного плана диеты

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

        try:
            # Получаем текущий план диеты
            diet_plan = await self.diet_service.get_current_diet(user_id)
            if not diet_plan:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Diet.Full.NO_PLAN, lang)
                }

            # Получаем данные о пользователе
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.User.NOT_FOUND, lang)
                }

            # Получаем текст запроса из параметров
            if not params or "update_request" not in params:
                # Пытаемся получить текст из других возможных мест в параметрах
                update_request = None
                if "params" in params:
                    if isinstance(params["params"], tuple) and len(params["params"]) > 0:
                        update_request = params["params"][0]
                    elif isinstance(params["params"], dict) and "update_request" in params["params"]:
                        update_request = params["params"]["update_request"]

                if not update_request:
                    self.logger.error("Update request text not found in parameters")
                    return {
                        "success": False,
                        "message": self.get_localized_message(LK.Diet.Update.INVALID_FORMAT, lang)
                    }
            else:
                update_request = params["update_request"]

            # Сообщаем пользователю, что обновляем план
            recipient_id = user.get("phone_number", "")
            await self.messenger_service.send_message(
                recipient_id,
                self.get_localized_message(LK.Messaging.UPDATING_PLAN, lang),
                {"user_id": user_id}
            )

            # TODO переработать через контекст сервис
            # Получаем контекст пользователя для извлечения команд
            user_context = await self._get_user_conversation_context(user["id"])

            # Дополняем контекст информацией о текущем состоянии
            context_with_state = await self._enrich_context_with_state(user_context, user["id"])

            # Обновляем полный план диеты
            result = await self.diet_service.update_diet_plan(
                diet_plan["id"],
                update_request,
                context_with_state
            )

            if "error" in result:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Diet.Full.UPDATE_FAILED, lang)
                }

            # Формируем и отправляем сообщение о результате обновления
            if "success" in result and result["success"]:
                # Используем форматтер для получения сообщения об успешном обновлении
                from app.services.formatter.diet_update_formatter import DietUpdateFormatter
                formatter = DietUpdateFormatter(self.localization_service)

                updated_days_keys = list(result.get("updated_days", {}).keys())
                comment = result.get("comment", self.get_localized_message(LK.Diet.Update.DEFAULT_COMMENT, lang))

                update_message = formatter.format_update_success_message(
                    comment,
                    updated_days_keys,
                    lang
                )

                messages = [update_message]

                return {
                    "success": True,
                    "messages": messages,
                    "updated_days": updated_days_keys
                }
            else:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Diet.Full.UPDATE_FAILED, lang)
                }

        except Exception as e:
            self.logger.error(f"Error executing full diet update command: {str(e)}")
            return {
                "success": False,
                "message": self.get_localized_message(LK.Diet.Full.UPDATE_FAILED, lang)
            }

    async def _get_user_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """
        Получает контекст разговора пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Dict[str, Any]: Контекст разговора
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user or "last_conversation_context" not in user:
            return {}

        return user.get("last_conversation_context", {})

    async def _enrich_context_with_state(self, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Дополняет контекст информацией о текущем состоянии пользователя

        Args:
            context: Исходный контекст
            user_id: ID пользователя

        Returns:
            Dict[str, Any]: Дополненный контекст
        """
        enriched = context.copy() if context else {}

        try:
            # Получаем пользователя для определения часового пояса
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return enriched

            # Получаем трекинговую дату
            tracking_date = DateHelper.get_tracking_date(user.get("timezone"))

            # Проверяем наличие плана диеты
            current_diet = await self.diet_service.get_current_diet(user_id)
            if current_diet:
                enriched["has_diet_plan"] = True
                enriched["diet_plan_id"] = current_diet.get("id")

                # Добавляем информацию о днях плана питания
                if "daily_plans" in current_diet:
                    enriched["current_diet_days"] = list(current_diet["daily_plans"].keys())

                # Получаем план на сегодня для детального контекста
                today_plan = await self.diet_service.get_diet_for_day(user_id, tracking_date)
                if today_plan:
                    enriched["today_diet_plan"] = {
                        "date": tracking_date.isoformat(),
                        "day_of_week": DateHelper.get_day_of_week(tracking_date),
                        "meals": today_plan.get("meals", []),
                        "total_calories": today_plan.get("total_calories", 0),
                        "total_proteins": today_plan.get("total_proteins", 0),
                        "total_fats": today_plan.get("total_fats", 0),
                        "total_carbs": today_plan.get("total_carbs", 0)
                    }

            daily_tracking = await self.tracking_service.get_daily_tracking_history(user_id, tracking_date)
            if daily_tracking:
                enriched["daily_tracking_history"] = daily_tracking

                # Добавляем краткую сводку для удобства LLM
                enriched["tracking_summary"] = {
                    "completed_meals": [
                        meal_type for meal_type, meal_data in daily_tracking.get("meals_tracking", {}).items()
                        if meal_data.get("status") in ["followed", "partially", "substituted"]
                    ],
                    "skipped_meals": [
                        meal_type for meal_type, meal_data in daily_tracking.get("meals_tracking", {}).items()
                        if meal_data.get("status") == "skipped"
                    ],
                    "total_calories_consumed": daily_tracking.get("cumulative_nutrients", {}).get("calories", 0),
                    "total_proteins_consumed": daily_tracking.get("cumulative_nutrients", {}).get("proteins", 0),
                    "total_fats_consumed": daily_tracking.get("cumulative_nutrients", {}).get("fats", 0),
                    "total_carbs_consumed": daily_tracking.get("cumulative_nutrients", {}).get("carbs", 0),
                    "water_consumed": daily_tracking.get("daily_totals", {}).get("water_consumed", 0),
                    "compliance_score": daily_tracking.get("overall_compliance_score", 0)
                }

            # Получаем последние данные о весе
            weight_entries = await self.tracking_service.get_recent_weight_entries(user_id, 1)
            if weight_entries:
                enriched["latest_weight"] = weight_entries[0].get("weight")
                enriched["latest_weight_date"] = weight_entries[0].get("date")

            # Получаем последний план с ожиданием согласования
            pending_plan = await self.diet_service.get_pending_diet_plan(user_id)
            if pending_plan:
                enriched["has_pending_diet_plan"] = True
                enriched["pending_plan_id"] = pending_plan.get("id")

        except Exception as e:
            self.logger.error(f"Error enriching context with state: {str(e)}")

        return enriched

    def get_error_message(self, lang: str = None) -> str:
        """
        Получение сообщения об ошибке

        Args:
            lang: Язык пользователя

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Diet.Full.NO_PLAN, lang)


class DietUpdateCommand(BaseCommand):
    """
    Общая команда обновления плана диеты, которая делегирует выполнение
    соответствующей команде в зависимости от типа плана
    """

    async def can_execute(self, user_id: str) -> bool:
        """
        Проверяет возможность выполнения команды обновления плана диеты

        Args:
            user_id: ID пользователя

        Returns:
            bool: Возможность выполнения команды
        """
        try:
            # Проверяем наличие активного плана
            diet_plan = await self.diet_service.get_current_diet(user_id)
            return diet_plan is not None
        except Exception as e:
            self.logger.error(f"Error checking diet update prerequisites: {str(e)}")
            return False

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды обновления плана диеты
        через делегирование соответствующей команде

        Args:
            user_id: ID пользователя
            params: Параметры команды

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        try:
            # Получаем текущий план диеты
            diet_plan = await self.diet_service.get_current_diet(user_id)

            # Создаем соответствующую команду
            if diet_plan and diet_plan.get("version") == "short" and diet_plan.get("status") == "pending":
                command = ShortDietUpdateCommand(self.dependencies)
            else:
                command = FullDietUpdateCommand(self.dependencies)

            # Формируем итоговый результат в правильном порядке
            final_result = {
                "success": True,
            }

            # Выполняем команду обновления
            update_result = await command.execute(user_id, params)

            # Если обновление было успешным, вызываем команду диеты для отображения обновленного плана
            if update_result.get("success", False):

                if "updated_days" in update_result:
                    # Создаем экземпляр команды диеты
                    diet_command = DietCommand(self.dependencies)

                    for day_name in update_result["updated_days"]:
                        # Выполняем команду диеты для отображения обновленного плана
                        diet_result = await diet_command.execute(user_id, params={'day': day_name})

                        # Если в diet_result есть сообщения, копируем их в итоговый результат
                        if "messages" in diet_result:
                            final_result["messages"] = diet_result.get("messages", []).copy()
                        elif "message" in diet_result:
                            final_result["messages"] = [diet_result["message"]]
                        else:
                            final_result["messages"] = {}

                # Теперь добавляем сообщение об обновлении в конец списка сообщений
                if "message" in update_result:
                    final_result["messages"].append(update_result["message"])
                elif "messages" in update_result:
                    final_result["messages"].extend(update_result["messages"])

                return final_result

            return update_result

        except Exception as e:
            # Получаем язык пользователя для локализации сообщения об ошибке
            lang = None
            if hasattr(self, 'localization_service') and self.localization_service:
                lang = await self.localization_service.get_user_language(user_id)

            self.logger.error(f"Error executing diet update command: {str(e)}")
            return {
                "success": False,
                "message": self.get_localized_message(LK.Diet.Update.UPDATE_FAILED, lang)
            }

    def get_error_message(self, lang: str = None) -> str:
        """
        Получение сообщения об ошибке

        Args:
            lang: Язык пользователя

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Messaging.NO_DIET_PLAN, lang)
