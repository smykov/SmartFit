# app/services/messaging/command_execution/command_executor.py
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio

import pytz

from app.models.command import Command, CommandStatus
from app.constants.localization_keys import LocalizationKeys as LK
from app.services.commands.command_factory import CommandFactory
from app.services.diet.diet_service_interface import IDietService
from app.services.messaging.interfaces.message_interface import IMessengerService
from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.localization.localization_interface import ILocalizationService
from config import settings


class CommandExecutor:
    """Сервис для выполнения команд, извлеченных из сообщений пользователя"""

    def __init__(self,
                 command_factory: CommandFactory,
                 messenger_service: IMessengerService,
                 diet_service: IDietService,
                 user_repository: IUserRepository,
                 localization_service: ILocalizationService):
        """
        Инициализация исполнителя команд

        Args:
            command_factory: Фабрика команд
            messenger_service: Сервис отправки сообщений
            user_repository: Репозиторий пользователей
            localization_service: Сервис локализации
        """
        self.command_factory = command_factory
        self.messenger_service = messenger_service
        self.diet_service = diet_service
        self.user_repository = user_repository
        self.localization_service = localization_service
        self.logger = logging.getLogger(self.__class__.__name__)

        # Маппинг LLM-команд к командам системы
        self.command_mapping = {
            "diet_update": "diet_update",
            "diet_approval": "diet_approval",
            "weight_record": "weight",
            "water_record": "water",
            "meal_compliance": "meal_compliance",
            "show_diet_plan": "diet",
            "show_shopping_list": "shopping_list",
            "general_response": None,  # Специальная обработка
            # Прямые маппинги
            "weight": "weight",
            "water": "water",
            "diet": "diet",
            "shopping_list": "shopping_list",
            "stats": "stats",
            "help": "help"
        }

    def get_localized_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        """
        Получает локализованное сообщение

        Args:
            key: Ключ сообщения
            lang: Код языка
            **params: Параметры для форматирования

        Returns:
            str: Локализованное сообщение
        """
        if self.localization_service:
            return self.localization_service.get_message(key, lang, **params)
        return key

    async def execute_commands(self,
                               user_id: str,
                               commands: List[Command],
                               messenger_type: str) -> Dict[str, Any]:
        """
        Выполняет список команд для пользователя

        Args:
            user_id: ID пользователя
            commands: Список команд для выполнения
            messenger_type: Тип мессенджера

        Returns:
            Dict[str, Any]: Результат выполнения команд
        """
        if not commands:
            return {"success": True, "action": "no_commands", "results": []}

        # Получаем пользователя
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            self.logger.error(f"User not found: {user_id}")
            return {"success": False, "error": "User not found"}

        # Отправитель для сообщений (номер телефона или chat_id)
        recipient_id = user.get("phone_number")
        if not recipient_id:
            self.logger.error(f"Recipient ID not found for user: {user_id}")
            return {"success": False, "error": "Recipient ID not found"}

        # Группируем команды по приоритету
        commands_by_priority = {}
        for command in commands:
            priority = command.priority
            if priority not in commands_by_priority:
                commands_by_priority[priority] = []
            commands_by_priority[priority].append(command)

        # Результаты выполнения команд
        results = []

        # Выполняем команды группами по приоритету
        for priority in sorted(commands_by_priority.keys()):
            priority_commands = commands_by_priority[priority]

            # Параллельно выполняем команды с одинаковым приоритетом
            group_results = await asyncio.gather(*[
                self._execute_single_command(user_id, cmd, messenger_type)
                for cmd in priority_commands
            ])

            results.extend(group_results)

        # Собираем общий результат
        success = all(result.get("success", False) for result in results)
        return {
            "success": success,
            "action": "commands_executed",
            "results": results
        }


    async def _execute_single_command(self,
                                      user_id: str,
                                      command: Command,
                                      messenger_type: str) -> Dict[str, Any]:
        """
        Выполняет одиночную команду

        Args:
            user_id: ID пользователя
            command: Команда для выполнения
            messenger_type: Тип мессенджера

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        try:
            # Получаем пользователя
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return {"success": False, "error": "User not found", "command": command.command_type}

            # Получаем язык пользователя
            lang = await self.localization_service.get_user_language(user_id)

            # Обрабатываем специальные команды
            if command.command_type == "general_response":
                # Это просто текстовый ответ, отправляем его пользователю
                response_text = command.params.get("response_text")
                if response_text:
                    await self.messenger_service.send_message(
                        user.get("phone_number"),
                        response_text,
                        {"user_id": user_id, "messenger_type": messenger_type}
                    )
                    return {"success": True, "action": "response_sent", "command": command.command_type}
                return {"success": False, "error": "No response text provided", "command": command.command_type}

            system_command_type = self.command_mapping.get(command.command_type)
            if not system_command_type:
                self.logger.warning(f"Unknown command type: {command.command_type}")
                return {"success": False, "error": f"Unknown command type: {command.command_type}",
                        "command": command.command_type}

            # Создаем команду через фабрику
            system_command = self.command_factory.create_command(system_command_type)
            if not system_command:
                self.logger.warning(f"Failed to create command: {system_command_type}")
                return {"success": False, "error": f"Failed to create command: {system_command_type}",
                        "command": command.command_type}


            # Проверяем возможность выполнения
            if not await system_command.can_execute(user_id):
                error_message = system_command.get_error_message(lang)

                # Отправляем ошибку пользователю
                await self.messenger_service.send_message(
                    user.get("phone_number"),
                    error_message,
                    {"user_id": user_id, "messenger_type": messenger_type}
                )

                return {"success": False, "error": error_message, "command": command.command_type}

            # Выполняем команду
            self.logger.info(f"Executing command {command.command_type} for user {user_id}")

            # Если команда meal_compliance, форматируем параметры правильно
            if command.command_type == "meal_compliance":
                # Преобразуем параметры в формат, ожидаемый ComplianceCommand
                system_params = {'params': []}

                if 'status' in command.params:
                    system_params['params'].append(command.params['status'])

                if 'meal_type' in command.params:
                    system_params['params'].append(command.params['meal_type'])

                result = await system_command.execute(user_id, system_params)
            else:
                # Для других команд используем параметры как есть
                result = await system_command.execute(user_id, command.params)

            # Если команда вернула сообщение, отправляем его пользователю
            if "message" in result and result["message"]:
                await self.messenger_service.send_message(
                    user.get("phone_number"),
                    result["message"],
                    {"user_id": user_id, "messenger_type": messenger_type}
                )

            # Если команда вернула несколько сообщений, отправляем их пользователю
            if "messages" in result and result["messages"]:
                await self.messenger_service.send_messages(
                    user.get("phone_number"),
                    result["messages"],
                    {"user_id": user_id, "messenger_type": messenger_type}
                )

            return {**result, "command": command.command_type}

        except Exception as e:
            self.logger.error(f"Error executing command {command.command_type}: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e), "command": command.command_type}

    def _is_today_updated(self, updated_days: Dict[str, Any], today=None) -> bool:
        """
        Проверяет, был ли обновлен план на сегодня

        Args:
            updated_days: Словарь обновленных дней
            today: Дата сегодня (если None, будет получена автоматически)

        Returns:
            bool: True, если был обновлен план на сегодня
        """
        if not updated_days:
            return False

        # Получаем текущую дату, если не передана
        if today is None:
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

        # Проверяем по ISO формату
        today_iso = today.isoformat()
        if today_iso in updated_days:
            return True

        # Проверяем по дню недели
        day_of_week = today.strftime("%A").lower()
        if day_of_week in updated_days:
            return True

        return False

    # Расширим CommandExecutor для лучшей обработки diet_update команд

    def _transform_params(self, command_type: str, cmd_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует параметры из формата LLM в формат команд системы

        Args:
            command_type: Тип команды
            cmd_data: Данные команды

        Returns:
            Dict[str, Any]: Преобразованные параметры
        """
        params = {}

        # Получаем параметры из LLM ответа
        if "parameters" in cmd_data and isinstance(cmd_data["parameters"], list):
            for param in cmd_data["parameters"]:
                if isinstance(param, dict) and "name" in param and "value" in param:
                    params[param["name"]] = param["value"]

        # Особая обработка для diet_update
        if command_type == "diet_update":
            # Строим структурированный запрос на обновление
            parts = []

            # Сначала обрабатываем удаление продуктов
            if "foods_to_remove" in params and params["foods_to_remove"]:
                products = ", ".join(params["foods_to_remove"])
                parts.append(f"Убрать {products}")

            # Затем обрабатываем замены продуктов
            if "foods_to_replace" in params and params["foods_to_replace"]:
                replacements = []
                replacements_data = params["foods_to_replace"]

                # Обрабатываем различные форматы данных замены
                if isinstance(replacements_data, list):
                    for repl in replacements_data:
                        if isinstance(repl, list) and len(repl) == 2:
                            replacements.append(f"{repl[0]} на {repl[1]}")
                        elif isinstance(repl, dict) and "from" in repl and "to" in repl:
                            replacements.append(f"{repl['from']} на {repl['to']}")

                if replacements:
                    parts.append(f"Заменить {', '.join(replacements)}")

            # Добавляем информацию о приемах пищи, если указана
            if "meal_types" in params and params["meal_types"]:
                meal_type_names = {
                    "breakfast": "завтрак",
                    "lunch": "обед",
                    "dinner": "ужин",
                    "snack": "перекус"
                }

                meal_types = []
                for meal in params["meal_types"]:
                    meal_type = meal_type_names.get(meal.lower(), meal)
                    meal_types.append(meal_type)

                if meal_types:
                    parts.append(f"Для приемов пищи: {', '.join(meal_types)}")

            # Добавляем информацию о днях, если указаны
            if "days" in params and params["days"]:
                day_names = {
                    "monday": "понедельник",
                    "tuesday": "вторник",
                    "wednesday": "среда",
                    "thursday": "четверг",
                    "friday": "пятница",
                    "saturday": "суббота",
                    "sunday": "воскресенье"
                }

                days = []
                for day in params["days"]:
                    day_name = day_names.get(day.lower(), day)
                    days.append(day_name)

                if days:
                    parts.append(f"В дни: {', '.join(days)}")

            # Собираем финальный запрос для обновления
            update_request = ". ".join(parts)

            # Если оригинальное сообщение короче и понятнее, используем его
            if "original_message" in params and len(params["original_message"]) <= len(update_request):
                update_request = params["original_message"]

            # Если сформированный запрос пуст, но есть важные параметры, добавляем их напрямую
            if not update_request and (params.get("foods_to_remove") or params.get("foods_to_replace")):
                update_request = "Обновить план питания с указанными изменениями продуктов"

            self.logger.debug(f"Transformed diet_update request: {update_request}")

            # Возвращаем подготовленный запрос для обработки
            return {"update_request": update_request}

        # Обработка weight_record
        elif command_type == "weight_record":
            # Преобразуем в формат, ожидаемый WeightCommand
            weight = params.get("weight")
            if weight is not None:
                return {"params": (str(weight),)}

        # Обработка water_record
        elif command_type == "water_record":
            # Преобразуем в формат, ожидаемый WaterCommand
            amount = params.get("amount")
            if amount is not None:
                return {"params": (str(amount),)}

        # Обработка meal_compliance
        elif command_type == "meal_compliance":
            # Преобразуем в формат, ожидаемый ComplianceCommand
            meal_type = params.get("meal_type")
            status = params.get("status")
            if meal_type and status:
                return {"params": (status, meal_type)}

        # Для остальных типов команд возвращаем параметры как есть
        return params