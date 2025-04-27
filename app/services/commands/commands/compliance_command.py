# app/services/commands/commands/compliance_command.py
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

import pytz

from app.services.commands.base_command import BaseCommand
from app.models.tracking import MealComplianceStatus
from app.constants.localization_keys import LocalizationKeys as LK
from config import settings


class ComplianceCommand(BaseCommand):
    """
    Команда для отметки о соблюдении плана питания
    """

    def __init__(self, dependencies: Dict[str, Any]):
        """
        Инициализация команды с зависимостями

        Args:
            dependencies: Словарь зависимостей для команды
        """
        super().__init__(dependencies)
        self._status_mapping = None
        self._meal_type_mapping = None
        self._meal_type_display_mapping = None

    async def can_execute(self, user_id: str) -> bool:
        """Проверка возможности выполнения команды"""
        try:
            # Проверяем наличие плана диеты
            diet_plan = await self.diet_service.get_current_diet(user_id)
            return diet_plan is not None
        except Exception as e:
            self.logger.error(f"Error checking compliance command prerequisites: {str(e)}")
            return False

    def _initialize_mappings(self, lang: str = None) -> None:
        """
        Инициализирует маппинги для статусов и типов приема пищи

        Args:
            lang: Код языка для локализации
        """
        if self._status_mapping is not None:
            # Маппинги уже инициализированы
            return

        self.logger.info(f"Initializing compliance mappings (user language: {lang or 'default'})")

        # Маппинг ключей LK к статусам MealComplianceStatus
        self._status_mapping = {
            LK.Commands.Compliance.FOLLOWED: MealComplianceStatus.FOLLOWED,
            LK.Commands.Compliance.PARTIALLY: MealComplianceStatus.PARTIALLY,
            LK.Commands.Compliance.SUBSTITUTED: MealComplianceStatus.SUBSTITUTED,
            LK.Commands.Compliance.SKIPPED: MealComplianceStatus.SKIPPED
        }

        # Создаем словари ключевых слов для статусов и типов приема пищи
        # для каждого поддерживаемого языка
        self._status_keyword_mapping = {}
        self._meal_type_mapping = {}
        self._meal_type_display_mapping = {}

        for lang_code in ["ru", "en", "es"]:
            # Сопоставление ключевых слов статусов с enum статусов
            status_words = {}
            for key, status in self._status_mapping.items():
                localized_word = self.get_localized_message(key, lang_code).lower()
                if localized_word:
                    status_words[localized_word] = status
                    # Добавляем числовые альтернативы для индексов статусов
                    if status == MealComplianceStatus.FOLLOWED:
                        status_words["1"] = status
                    elif status == MealComplianceStatus.PARTIALLY:
                        status_words["2"] = status
                    elif status == MealComplianceStatus.SUBSTITUTED:
                        status_words["3"] = status
                    elif status == MealComplianceStatus.SKIPPED:
                        status_words["4"] = status

            self._status_keyword_mapping[lang_code] = status_words

            # Сопоставление типов приема пищи
            meal_types = {}
            meal_display = {}
            for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
                # Получаем локализованное название типа приема пищи
                localized_meal = self.get_localized_message(f"common.meal_types.{meal_type}", lang_code).lower()
                if localized_meal:
                    meal_types[localized_meal] = meal_type
                    meal_display[meal_type] = self.get_localized_message(f"common.meal_types.{meal_type}", lang_code)
                    # Добавляем числовые альтернативы для индексов приемов пищи
                    if meal_type == "breakfast":
                        meal_types["1"] = meal_type
                    elif meal_type == "lunch":
                        meal_types["2"] = meal_type
                    elif meal_type == "dinner":
                        meal_types["3"] = meal_type
                    elif meal_type == "snack":
                        meal_types["4"] = meal_type

            self._meal_type_mapping[lang_code] = meal_types
            self._meal_type_display_mapping[lang_code] = meal_display

        self.logger.info(f"Compliance mappings initialized successfully")

    def _get_status_from_text(self, text: str, lang: str = None) -> Optional[MealComplianceStatus]:
        """
        Определяет статус соблюдения из текста сообщения

        Args:
            text: Текст пользователя
            lang: Код языка

        Returns:
            Optional[MealComplianceStatus]: Статус соблюдения или None
        """
        text = text.lower().strip()

        # Проверяем, инициализированы ли маппинги
        self._initialize_mappings(lang)

        # Проверяем на совпадение для всех поддерживаемых языков
        for lang_code, keyword_map in self._status_keyword_mapping.items():
            # Проверяем точное соответствие
            if text in keyword_map:
                return keyword_map[text]

            # Проверяем наличие ключевых слов в тексте
            for keyword, status in keyword_map.items():
                if len(keyword) > 1 and keyword in text:
                    return status

        return None

    def _get_meal_type_from_text(self, text: str, lang: str = None) -> Optional[str]:
        """
        Определяет тип приема пищи из текста сообщения

        Args:
            text: Текст пользователя
            lang: Код языка

        Returns:
            Optional[str]: Внутренний код типа приема пищи или None
        """
        text = text.lower().strip()

        # Проверяем, инициализированы ли маппинги
        self._initialize_mappings(lang)

        # Проверяем на совпадение для всех поддерживаемых языков
        for lang_code, meal_map in self._meal_type_mapping.items():
            # Проверяем точное соответствие
            if text in meal_map:
                return meal_map[text]

            # Проверяем наличие ключевых слов в тексте
            for keyword, meal_type in meal_map.items():
                if len(keyword) > 1 and keyword in text:
                    return meal_type

        return None

    def _get_localized_meal_type_display(self, meal_type: str, lang: str = None) -> str:
        """
        Возвращает локализованное отображаемое имя типа приема пищи

        Args:
            meal_type: Внутренний код типа приема пищи
            lang: Код языка

        Returns:
            str: Локализованное название типа приема пищи
        """
        # Проверяем, инициализированы ли маппинги
        self._initialize_mappings(lang)

        # Пытаемся найти локализованное отображение на конкретном языке
        if lang and lang in self._meal_type_display_mapping:
            if meal_type in self._meal_type_display_mapping[lang]:
                return self._meal_type_display_mapping[lang][meal_type]

        # Если не найдено, используем первый доступный язык
        for lang_code, display_map in self._meal_type_display_mapping.items():
            if meal_type in display_map:
                return display_map[meal_type]

        # Если ничего не найдено, возвращаем оригинальный код
        return meal_type

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
            # Получаем язык пользователя
            lang = None
            if hasattr(self, 'localization_service') and self.localization_service:
                lang = await self.localization_service.get_user_language(user_id)

            # Инициализируем маппинги с учетом языка пользователя
            self._initialize_mappings(lang)

            self.logger.info(f"Processing compliance command: params: {params}")

            # Проверяем наличие параметров
            if not params or 'params' not in params:
                self.logger.error("Error recording compliance: no parameters provided")
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.INVALID_FORMAT, lang)
                }

            # Получаем текст сообщения и выполняем предварительную очистку
            command_params = params.get('params', [])
            if len(command_params) < 2:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.INVALID_FORMAT, lang)
                }

            status = None
            meal_type = None

            if 'status' in params:
                status = params['status']
            elif 'params' in params and len(params['params']) > 0:
                status = params['params'][0]

            if 'meal_type' in params:
                meal_type = params['meal_type']
            elif 'params' in params and len(params['params']) > 1:
                meal_type = params['params'][1]

            # Проверяем корректность значений
            if not status or not meal_type:
                self.logger.error(f"Invalid status or meal type: status={status}, meal_type={meal_type}")
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.INVALID_TYPE, lang)
                }

            self.logger.info(f"Recording compliance: type={meal_type}, status={status}")

            # Получаем текущую дату
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Проверяем наличие плана диеты
            diet_plan = await self.diet_service.get_current_diet(user_id)

            if not diet_plan:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.NO_DIET_PLAN, lang)
                }

            try:
                # Записываем соблюдение через трекинг-сервис
                result = await self.tracking_service.record_meal_compliance(
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
                        "message": self.get_localized_message(LK.Commands.Compliance.RECORD_ERROR, lang)
                    }

                # Получаем данные о соблюдении плана
                compliance_data = await self.tracking_service.get_diet_compliance(user_id, today)

                # Получаем локализованное отображение типа приема пищи
                meal_type_display = self._get_localized_meal_type_display(meal_type, lang)

                # Получаем форматтер для отображения сообщения
                tracking_formatter = self.dependencies.get('tracking_formatter_service')
                if tracking_formatter:
                    message = tracking_formatter.format_compliance_message(
                        meal_type_display,
                        status,
                        compliance_data,
                        lang
                    )
                else:
                    # Если форматтер недоступен, формируем простое сообщение
                    status_key = None
                    for lk, status_value in self._status_mapping.items():
                        if status_value == status:
                            status_key = lk
                            break

                    status = self.get_localized_message(status_key, lang) if status_key else str(status)

                    message = self.get_localized_message(
                        LK.Commands.Compliance.RECORDED,
                        lang,
                        meal_type=meal_type_display,
                        status=status
                    )

                return {
                    "success": True,
                    "message": message
                }

            except Exception as e:
                self.logger.error(f"Error recording compliance: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.RECORD_ERROR, lang)
                }

        except Exception as e:
            self.logger.error(f"Error processing compliance command: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Compliance.RECORD_ERROR, lang)
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Commands.Compliance.INVALID_FORMAT)
