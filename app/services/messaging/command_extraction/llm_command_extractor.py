# app/services/messaging/command_extraction/llm_command_extractor.py
import json
import logging
import re
from typing import Dict, Any, List, Optional

from app.constants.localization_keys import LocalizationKeys as LK
from app.db.interfaces.diet_plan_repository_interface import IDietPlanRepository
from app.models.command import Command, CommandExtractionResult, CommandSource
from app.services.formatter.diet_data_transformer import DietDataTransformer
from app.services.messaging.command_extraction.command_extraction_interface import ICommandExtractor
from app.services.llm.base_llm_service import BaseLLMService
from app.db.interfaces.user_repository_interface import IUserRepository
from app.templates.prompts import create_command_extraction_system_prompt, create_command_extraction_user_prompt
from app.templates.formatting_helpers import clean_json_from_markdown
from app.utils.date_helper import DateHelper


class LLMCommandExtractor(ICommandExtractor):
    """Экстрактор команд, использующий языковую модель (LLM)"""

    def __init__(self,
                 llm_service: BaseLLMService,
                 user_repository: IUserRepository,
                 diet_plan_repository: IDietPlanRepository,
                 min_confidence: float = 0.7):
        """
        Инициализация экстрактора команд

        Args:
            llm_service: Сервис языковой модели
            user_repository: Репозиторий пользователей
            min_confidence: Минимальный порог уверенности для применения команд
        """
        self.llm_service = llm_service
        self.user_repository = user_repository
        self.diet_plan_repository = diet_plan_repository
        self.min_confidence = min_confidence
        self.logger = logging.getLogger(self.__class__.__name__)

        # Регулярные выражения для базовых команд (как запасной вариант)
        self.command_patterns = {
            "weight": re.compile(r'^вес\s+(\d+[.,]?\d*)$', re.IGNORECASE),
            "water": re.compile(r'^вода\s+(\d+[.,]?\d*)$', re.IGNORECASE),
            "help": re.compile(r'^(помощь|справка|команды|help)$', re.IGNORECASE),
            "diet": re.compile(r'^(диета|план|план питания|меню)$', re.IGNORECASE),
            "shopping_list": re.compile(r'^список покупок$', re.IGNORECASE),
            "stats": re.compile(r'^(статистика|прогресс)$', re.IGNORECASE),
            "meal_compliance": re.compile(r'^(выполнено|частично|заменил[а]?|пропустил[а]?|1|2|3|4)\s+(завтрак|обед|ужин|перекус)$',
                                          re.IGNORECASE),
            "diet_update": re.compile(r'^(измени|поменяй|обнови|замени|скорректируй)\s+(план|меню|рацион|питание)(.*)$',
                                      re.IGNORECASE),
        }

    async def extract_commands(self, message: str, user_id: str,
                               context: Dict[str, Any] = None) -> CommandExtractionResult:
        """
        Извлекает команды из текстового сообщения пользователя

        Args:
            message: Текст сообщения
            user_id: ID пользователя
            context: Контекст пользователя и разговора

        Returns:
            CommandExtractionResult: Результат извлечения с командами и ответом
        """
        try:
            # Сначала проверяем через простые паттерны
            pattern_result = self._extract_via_patterns(message)
            if pattern_result:
                self.logger.info(f"Extracted command via pattern matching: {pattern_result.commands[0].command_type}")
                return pattern_result

            # Если через паттерны не получилось, используем LLM
            return await self._extract_via_llm(message, user_id, context or {})

        except Exception as e:
            self.logger.error(f"Error extracting commands: {str(e)}", exc_info=True)
            # В случае ошибки возвращаем результат с fallback на AI
            return CommandExtractionResult(
                commands=[],
                fallback_to_ai=False,
                response_message=self._ai_fallback_response(),
                execution_required=False,
                source=CommandSource.FALLBACK
            )

    def _ai_fallback_response(self) -> str:
        """
        Ответ по умолчанию при невозможности определить команду

        Returns:
            str: Стандартный ответ
        """

        # Общий ответ для неизвестных запросов
        return LK.Errors.AI_FALLBACK_RESPONSE

    def _extract_via_patterns(self, message: str) -> Optional[CommandExtractionResult]:
        """
        Пытается извлечь команду через регулярные выражения

        Args:
            message: Текст сообщения

        Returns:
            Optional[CommandExtractionResult]: Результат извлечения или None
        """
        for cmd_type, pattern in self.command_patterns.items():
            match = pattern.match(message)
            if match:
                # Создаем команду
                command = Command(
                    command_type=cmd_type,
                    params={"params": match.groups() if match.groups() else {}},
                    priority=0,
                    source=CommandSource.PATTERN_MATCH,
                    confidence=0.95
                )

                # Создаем результат
                return CommandExtractionResult(
                    commands=[command],
                    response_message=None,
                    fallback_to_ai=False,
                    execution_required=True,
                    source=CommandSource.PATTERN_MATCH
                )

        return None

    async def _extract_via_llm(self, message: str, user_id: str, context: Dict[str, Any]) -> CommandExtractionResult:
        """
        Извлекает команды через языковую модель

        Args:
            message: Текст сообщения
            user_id: ID пользователя
            context: Контекст пользователя и разговора

        Returns:
            CommandExtractionResult: Результат извлечения
        """
        # Получаем данные пользователя для контекста
        user = await self.user_repository.get_by_id(user_id)
        # Получаем данные по текущему плану для контекста
        current_diet = await self.diet_plan_repository.get_current_diet(user.get('id'))

        # Обогащаем контекст
        enriched_context = self._enrich_context(context, user, current_diet)

        # Создаем системный промпт
        system_prompt = create_command_extraction_system_prompt()

        # Создаем пользовательский промпт
        user_prompt = create_command_extraction_user_prompt(message, enriched_context)

        # Вызываем LLM
        self.logger.info(f"Calling LLM for command extraction: {message[:50]}...")
        # TODO отделить трекинг приемов пищи в отдельный промпт, и тогда убрать smart модель
        response = await self.llm_service.generate_completion(system_prompt, user_prompt, model="smart")

        # Очищаем ответ от маркдауна
        cleaned_response = clean_json_from_markdown(response)

        # Парсим JSON-ответ
        try:
            result_dict = json.loads(cleaned_response)

            # Преобразуем JSON в модель
            commands = []
            for cmd_data in result_dict.get("commands", []):
                command = Command(
                    command_type=cmd_data.get("command_type"),
                    params=self._transform_params(cmd_data),
                    priority=cmd_data.get("priority", 0),
                    source=CommandSource.LLM_EXTRACTION,
                    confidence=float(result_dict.get("confidence", 0.8))
                )
                commands.append(command)

            return CommandExtractionResult(
                commands=commands,
                response_message=result_dict.get("response_message"),
                fallback_to_ai=len(commands) == 0,
                execution_required=True,
                source=CommandSource.LLM_EXTRACTION
            )

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            self.logger.debug(f"Raw LLM response: {response}")

            # Пытаемся применить запасной парсинг
            extracted_commands = self._fallback_extraction(message, response)

            if extracted_commands:
                return CommandExtractionResult(
                    commands=extracted_commands,
                    response_message=None,
                    fallback_to_ai=False,
                    execution_required=True,
                    source=CommandSource.FALLBACK
                )

            # Если ничего не получилось
            return CommandExtractionResult(
                commands=[],
                response_message=self._ai_fallback_response(),
                fallback_to_ai=False,
                execution_required=False,
                source=CommandSource.FALLBACK
            )

    def _enrich_context(self, context: Dict[str, Any], user: Optional[Dict[str, Any]],
                        current_diet: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Обогащает контекст данными пользователя

        Args:
            context: Исходный контекст
            user: Данные пользователя
            current_diet: Текущий план диеты

        Returns:
            Dict[str, Any]: Обогащенный контекст
        """
        enriched = context.copy() if context else {}
        # КРИТИЧЕСКИ ВАЖНАЯ временная информация (всегда включаем)
        user_timezone = user.get("timezone") if user else None
        time_context = DateHelper.get_context_for_llm(user_timezone)
        enriched.update(time_context)

        if user:
            # Основная информация о пользователе (минимум)
            enriched.update({
                "name": user.get("name", ""),
                "gender": user.get("gender", ""),
                "weight_goal": user.get("weight_goal", ""),
                "current_weight": user.get("current_weight", ""),
                "target_weight": user.get("target_weight", ""),
                "budget_limit": user.get("budget_limit", ""),
                "age": user.get("age", ""),
                "height": user.get("height", ""),
                "activity_level": user.get("activity_level", ""),
                "diet_preference": user.get("diet_preference", ""),
                "is_onboarding_completed": user.get("is_onboarding_completed", False),
                "language": user.get("language", ""),
                "currency_code": user.get("currency_code", "")
            })

            # Информация о диете (только критично важная)
            if current_diet:
                enriched["diet_plan"] = {
                    "status": current_diet.get('status'),
                    "version": current_diet.get('version'),
                    "has_plan": True,
                    "daily_plans": current_diet.get("daily_plans"),
                    "modifications_history": current_diet.get('modifications_history'),
                }

            else:
                enriched["diet_plan"] = {"has_plan": False}

            if user.get("allergies"):
                enriched["allergies"] = user.get("allergies", [])

            if user.get("disliked_products"):
                enriched["disliked_products"] = user.get("disliked_products", [])

            # добавить текущую информацию о трекинге воды, блюд
            # # Получаем последние данные о весе
            # weight_entries = await self.tracking_service.get_recent_weight_entries(user_id, 1)
            # if weight_entries:
            #     enriched["latest_weight"] = weight_entries[0].get("weight")
            #     enriched["latest_weight_date"] = weight_entries[0].get("date")
            #
            # # Получаем последний план с ожиданием согласования
            # pending_plan = await self.diet_service.get_pending_diet_plan(user_id)
            # if pending_plan:
            #     enriched["has_pending_diet_plan"] = True
            #     enriched["pending_plan_id"] = pending_plan.get("id")
            # Добавляем последний контекст разговора
            last_context = user.get("last_conversation_context", {})
            if last_context:
                enriched["last_action"] = last_context.get("last_action", "")
                enriched["last_message"] = last_context.get("last_message", "")

        return enriched

    def _transform_params(self, cmd_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует параметры из формата LLM в формат команд

        Args:
            cmd_data: Данные команды из LLM

        Returns:
            Dict[str, Any]: Преобразованные параметры
        """
        params = {}

        # Обработка массива параметров из LLM
        if "parameters" in cmd_data and isinstance(cmd_data["parameters"], list):
            for param in cmd_data["parameters"]:
                if isinstance(param, dict) and "name" in param and "value" in param:
                    params[param["name"]] = param["value"]

        command_type = cmd_data.get("command_type")
        # Специальная обработка для определенных типов команд
        if command_type == "diet_update":
            # Преобразуем параметры в текстовый запрос для обновления
            update_request = params.get("user_prompt")
            if update_request:
                params["update_request"] = update_request

        elif command_type in ["weight_record", "water_record"]:
            # Преобразуем числовое значение в кортеж для params
            value = params.get("weight") if command_type == "weight_record" else params.get("amount")
            if value is not None:
                params["params"] = (str(value),)

        return params

    def _fallback_extraction(self, message: str, llm_response: str) -> List[Command]:
        """
        Запасной метод извлечения команд при ошибке парсинга JSON

        Args:
            message: Исходное сообщение пользователя
            llm_response: Ответ LLM

        Returns:
            List[Command]: Извлеченные команды
        """
        # Пытаемся найти упоминания команд в ответе LLM
        commands = []

        # Поиск командных типов в тексте ответа
        command_types = re.findall(r'"command_type":\s*"([^"]+)"', llm_response)

        if command_types:
            # Для каждого найденного типа команды создаем объект
            for cmd_type in command_types:
                # Для других типов команд
                commands.append(Command(
                    command_type=cmd_type,
                    params={},
                    priority=0,
                    source=CommandSource.FALLBACK,
                    confidence=0.6
                ))

        return commands
