# app/services/messaging/command_extraction/llm_command_extractor.py (обновленная версия)
import json
import logging
import re
from typing import Dict, Any, List, Optional

from app.constants.localization_keys import LocalizationKeys as LK
from app.db.interfaces.diet_plan_repository_interface import IDietPlanRepository
from app.models.command import Command, CommandExtractionResult, CommandSource
from app.services.formatter.diet_data_transformer import DietDataTransformer
from app.services.localization.localization_interface import ILocalizationService
from app.services.messaging.command_extraction.command_extraction_interface import ICommandExtractor
from app.services.llm.base_llm_service import BaseLLMService
from app.db.interfaces.user_repository_interface import IUserRepository
from app.templates.prompts import create_command_extraction_system_prompt, create_command_extraction_user_prompt
from app.templates.formatting_helpers import clean_json_from_markdown
from app.utils.date_helper import DateHelper

# Импорты новых парсеров
from app.services.messaging.command_extraction.parsers.command_parser_registry import CommandParserRegistry
from app.services.messaging.command_extraction.parsers.diet_command_parser import DietCommandParser
from app.services.messaging.command_extraction.parsers.simple_command_parser import SimpleCommandParser


class LLMCommandExtractor(ICommandExtractor):
    """
    Экстрактор команд, использующий паттерн Registry для управления парсерами.
    """

    def __init__(self,
                 llm_service: BaseLLMService,
                 user_repository: IUserRepository,
                 diet_plan_repository: IDietPlanRepository,
                 localization_service: ILocalizationService,
                 min_confidence: float = 0.7):
        """
        Инициализация экстрактора команд

        Args:
            llm_service: Сервис языковой модели
            user_repository: Репозиторий пользователей
            diet_plan_repository: Репозиторий планов диеты
            localization_service: Сервис локализации
            min_confidence: Минимальный порог уверенности для применения команд
        """
        self.llm_service = llm_service
        self.user_repository = user_repository
        self.diet_plan_repository = diet_plan_repository
        self.localization_service = localization_service
        self.min_confidence = min_confidence
        self.logger = logging.getLogger(self.__class__.__name__)

        # Инициализируем реестр парсеров
        self.parser_registry = CommandParserRegistry()
        self._register_parsers()

        # Регулярные выражения для базовых команд (как запасной вариант)
        self.command_patterns = {
            "weight": re.compile(r'^вес\s+(\d+[.,]?\d*)$', re.IGNORECASE),
            "water": re.compile(r'^вода\s+(\d+[.,]?\d*)$', re.IGNORECASE),
            "help": re.compile(r'^(помощь|справка|команды|help)$', re.IGNORECASE),
            "diet": re.compile(r'^(диета|план|план питания|меню)$', re.IGNORECASE),
            "shopping_list": re.compile(r'^список покупок$', re.IGNORECASE),
            "stats": re.compile(r'^(статистика|прогресс)$', re.IGNORECASE),
            "meal_compliance": re.compile(
                r'^(выполнено|частично|заменил[а]?|пропустил[а]?|1|2|3|4)\s+(завтрак|обед|ужин|перекус)$',
                re.IGNORECASE),
            "diet_update": re.compile(r'^(измени|поменяй|обнови|замени|скорректируй)\s+(план|меню|рацион|питание)(.*)$',
                                      re.IGNORECASE),
        }

    def _register_parsers(self) -> None:
        """Регистрирует все парсеры команд"""
        # Регистрируем парсеры в порядке приоритета

        # 1. Парсер диетических команд (высокий приоритет)
        diet_parser = DietCommandParser(self.localization_service)
        self.parser_registry.register_parser(diet_parser)

        # 2. Парсер простых команд
        simple_parser = SimpleCommandParser()
        self.parser_registry.register_parser(simple_parser)

        # В будущем можно добавить другие парсеры:
        # self.parser_registry.register_parser(ComplexTrackingParser())
        # self.parser_registry.register_parser(ShoppingListParser())

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
            # Получаем пользователя и обогащаем контекст
            user = await self.user_repository.get_by_id(user_id)
            current_diet = await self.diet_plan_repository.get_current_diet(user_id)
            enriched_context = self._enrich_context(context or {}, user, current_diet)

            # 1. Сначала пробуем pattern matching через зарегистрированные парсеры
            pattern_commands = self.parser_registry.parse_message(message, enriched_context)

            if pattern_commands:
                command = pattern_commands[0]  # Берем первую найденную команду

                self.logger.info(f"Extracted command via pattern matching: {command.command_type}")
                return CommandExtractionResult(
                    commands=[command],
                    response_message=None,
                    fallback_to_ai=False,
                    execution_required=True,
                    source=CommandSource.PATTERN_MATCH
                )

            # 2. проверяем через простые паттерны
            # TODO убрать после перехода на парсеры
            pattern_result = self._extract_via_patterns(message)
            if pattern_result:
                self.logger.info(f"Extracted command via pattern matching: {pattern_result.commands[0].command_type}")
                return pattern_result

            # 3. Если pattern matching не сработал, используем LLM
            return await self._extract_via_llm(message, user_id, enriched_context)

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
        # Создаем системный промпт
        system_prompt = create_command_extraction_system_prompt()

        # Создаем пользовательский промпт
        user_prompt = create_command_extraction_user_prompt(message, context)

        # Вызываем LLM
        self.logger.info(f"Calling LLM for command extraction: {message[:50]}...")
        response = await self.llm_service.generate_completion(system_prompt, user_prompt)

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

            # Fallback на AI-ответ
            return CommandExtractionResult(
                commands=[],
                response_message=None,
                fallback_to_ai=True,
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
            # Основная информация о пользователе
            enriched.update({
                "user_name": user.get("name", ""),
                "user_gender": user.get("gender", ""),
                "user_weight_goal": user.get("weight_goal", ""),
                "current_weight": user.get("current_weight", ""),
                "target_weight": user.get("target_weight", ""),
                "budget_limit": user.get("budget_limit", ""),
                "age": user.get("age", ""),
                "activity_level": user.get("activity_level", ""),
                "diet_preference": user.get("diet_preference", ""),
                "is_onboarding_completed": user.get("is_onboarding_completed", False),
                "language": user.get("language", ""),
                "currency_code": user.get("currency_code", ""),
                "timezone": user_timezone
            })

            # Информация о диете
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

            # TODO добавить текущую информацию о трекинге воды и весе
            # Получаем последние данные о весе
            # weight_entries = await self.tracking_service.get_recent_weight_entries(user_id, 1)
            # if weight_entries:
            #     enriched["latest_weight"] = weight_entries[0].get("weight")
            #     enriched["latest_weight_date"] = weight_entries[0].get("date")
            #

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
            update_request = params.get("user_prompt")
            if update_request:
                params["update_request"] = update_request

        elif command_type in ["weight_record", "water_record"]:
            value = params.get("weight") if command_type == "weight_record" else params.get("amount")
            if value is not None:
                params["params"] = (str(value),)

        return params
