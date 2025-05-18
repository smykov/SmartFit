# app/services/commands/commands/diet_update_command.py
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Type

import pytz

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.commands.base_command import BaseCommand
from app.services.commands.commands.diet_command import DietCommand
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

    def _is_today_updated(self, updated_days: Dict[str, Any]) -> bool:
        """
        Проверяет, обновлен ли план на сегодня

        Args:
            updated_days: Словарь обновленных дней

        Returns:
            bool: True, если обновлен план на сегодня
        """
        if not updated_days:
            return False

        # Получаем текущую дату
        today = datetime.now(pytz.timezone(settings.TIMEZONE))

        # Проверяем по ISO формату
        today_iso = today.date().isoformat()
        if today_iso in updated_days.keys():
            return True

        # Проверяем по дню недели
        day_of_week = today.strftime("%A").lower()
        if day_of_week in updated_days.keys():
            return True

        return False


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
                    "message": update_message
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

            # Обновляем полный план диеты
            result = await self.diet_service.update_diet_plan(
                diet_plan["id"],
                update_request
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

                # Если был обновлен план на сегодня, отправляем его
                # if self._is_today_updated(result.get("updated_days", {})):
                #     today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()
                #     today_plan = self.diet_service.get_day_diet_plan(result["plan"], today, lang)
                #     if today_plan:
                #         messages.extend(today_plan)

                return {
                    "success": True,
                    "messages": messages
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

            # Выполняем команду обновления
            update_result = await command.execute(user_id, params)

            # Если обновление было успешным, вызываем команду диеты для отображения обновленного плана
            if update_result.get("success", False):
                # Создаем экземпляр команды диеты
                diet_command = DietCommand(self.dependencies)

                # Выполняем команду диеты для отображения обновленного плана
                diet_result = await diet_command.execute(user_id, params={'full': 'true'})

                # Формируем итоговый результат в правильном порядке
                # TOFIX TODO Сообщения идут не попорядку, сначала диета новая, а потом сообщения что диета была обновлена
                final_result = {
                    "success": True,
                }

                # Если в diet_result есть сообщения, копируем их в итоговый результат
                if "messages" in diet_result:
                    final_result["messages"] = diet_result.get("messages", []).copy()
                elif "message" in diet_result:
                    final_result["messages"] = [diet_result["message"]]
                else:
                    final_result["messages"] = []

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