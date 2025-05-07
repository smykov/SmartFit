# app/services/commands/commands/compliance_command.py
from typing import Dict, Any, Optional
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
        self.tracking_formatter_service = dependencies.get('tracking_formatter_service')

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
            params: Параметры команды
                - meal_type: тип приема пищи (breakfast, lunch, dinner, snack)
                - status: статус соблюдения (followed, partially, substituted, skipped)
                - user_report: текст с отчетом о приеме пищи от пользователя
                - calories: числовое значение употребленных калорий
                - proteins: числовое значение употребленных белков
                - fats: числовое значение употребленных жиров
                - carbs: числовое значение употребленных углеводов

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        # Получаем язык пользователя
        lang = None
        if hasattr(self, 'localization_service') and self.localization_service:
            lang = await self.localization_service.get_user_language(user_id)
        try:
            # Инициализируем маппинги с учетом языка пользователя
            self._initialize_mappings(lang)

            self.logger.info(f"Processing compliance command: params: {params}")

            status = None
            meal_type = None
            user_report = None
            nutrients_consumed = {}

            if params:
                # Формат 1: Прямые параметры от LLM
                if 'status' in params:
                    status = params['status']
                if 'meal_type' in params:
                    meal_type = params['meal_type']
                if 'user_report' in params:
                    user_report = params['user_report']

                # Собираем данные о нутриентах
                if 'calories' in params and params['calories'] is not None:
                    nutrients_consumed['calories'] = float(params['calories'])
                if 'proteins' in params and params['proteins'] is not None:
                    nutrients_consumed['proteins'] = float(params['proteins'])
                if 'fats' in params and params['fats'] is not None:
                    nutrients_consumed['fats'] = float(params['fats'])
                if 'carbs' in params and params['carbs'] is not None:
                    nutrients_consumed['carbs'] = float(params['carbs'])

                # Формат 2: Параметры с внутренним массивом 'params'
                if 'params' in params and isinstance(params['params'], list):
                    params_list = params['params']
                    if len(params_list) >= 2:
                        # Первый параметр обычно статус, второй - тип приема пищи
                        if not status and len(params_list) > 0:
                            status = params_list[0]
                        if not meal_type and len(params_list) > 1:
                            meal_type = params_list[1]

            # Логируем для диагностики
            self.logger.info(
                f"Extracted parameters: status={status}, meal_type={meal_type}, nutrients={nutrients_consumed}")

            # Проверяем валидность статуса и типа приема пищи
            status_enum = None
            if status is None:
                self.logger.error("Статус соблюдения не указан")
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.INVALID_TYPE, lang)
                }

            try:
                # Проверка соответствия статуса допустимым значениям
                if status in [s.value for s in MealComplianceStatus]:
                    status_enum = MealComplianceStatus(status)
                else:
                    self.logger.error(f"Неверный статус соблюдения: {status}")
                    return {
                        "success": False,
                        "message": self.get_localized_message(LK.Commands.Compliance.INVALID_TYPE, lang)
                    }
            except ValueError:
                self.logger.error(f"Неверный статус соблюдения: {status}")
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.INVALID_TYPE, lang)
                }

            if not meal_type:
                self.logger.error("Тип приема пищи не указан")
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.INVALID_MEAL_TYPE, lang)
                }

            self.logger.info(
                f"Recording compliance: type={meal_type}, status={status}, nutrients={nutrients_consumed}, user_report={user_report}")

            # Получаем текущую дату
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Проверяем наличие плана диеты
            # Получаем план на день (для отображения рекомендаций)
            day_plan = await self.diet_service.get_diet_for_day(user_id, today)

            if not day_plan:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.NO_DIET_PLAN, lang)
                }

            planned_meal = None

            if day_plan and "meals" in day_plan:
                for meal in day_plan.get("meals", []):
                    if meal.get("type") == meal_type:
                        planned_meal = meal
                        break

            try:
                # Записываем соблюдение через трекинг-сервис
                result = await self.tracking_service.record_meal_compliance(
                    user_id,
                    today,
                    meal_type,
                    status_enum,
                    user_report,  # отчёт пользователя
                    None,  # alternative_meal
                    nutrients_consumed  # данные о потреблённых нутриентах
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


                message = self.tracking_formatter_service.format_compliance_message(
                    meal_type_display,
                    status_enum.value,
                    compliance_data,
                    lang,
                    nutrients_consumed=nutrients_consumed,
                    planned_meal=planned_meal
                )

                # Добавляем рекомендации на основе соответствия плану
                if planned_meal and 'calories' in nutrients_consumed:
                    recommendations = self._generate_recommendations(
                        nutrients_consumed,
                        planned_meal,
                        lang
                    )

                    if recommendations:
                        message += f"\n\n{recommendations}"

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

    def _generate_recommendations(self,
                                  nutrients_consumed: Dict[str, float],
                                  planned_meal: Dict[str, Any],
                                  lang: Optional[str] = None) -> str:
        """
        Генерирует рекомендации на основе соответствия плану

        Args:
            nutrients_consumed: Словарь с данными о потреблённых нутриентах
            planned_meal: Запланированный приём пищи
            lang: Код языка

        Returns:
            str: Текст рекомендаций
        """
        try:
            recommendations = []

            # Анализ калорийности
            if 'calories' in nutrients_consumed and 'calories' in planned_meal:
                planned_calories = planned_meal['calories']
                actual_calories = nutrients_consumed['calories']
                calorie_ratio = actual_calories / planned_calories if planned_calories > 0 else 1.0

                # Значительное превышение калорий
                if calorie_ratio > 1.3:
                    recommendations.append(self.get_localized_message(
                        LK.Tracking.Compliance.CALORIES_EXCEEDED_SIGNIFICANTLY,
                        lang,
                        actual=actual_calories,
                        planned=planned_calories,
                        percent=round((calorie_ratio - 1) * 100)
                    ))
                # Небольшое превышение
                elif calorie_ratio > 1.1:
                    recommendations.append(self.get_localized_message(
                        LK.Tracking.Compliance.CALORIES_EXCEEDED_SLIGHTLY,
                        lang,
                        actual=actual_calories,
                        planned=planned_calories,
                        percent=round((calorie_ratio - 1) * 100)
                    ))
                # В рамках плана
                elif calorie_ratio >= 0.9:
                    recommendations.append(self.get_localized_message(
                        LK.Tracking.Compliance.CALORIES_ON_TARGET,
                        lang,
                        actual=actual_calories,
                        planned=planned_calories
                    ))
                # Ниже плана
                else:
                    recommendations.append(self.get_localized_message(
                        LK.Tracking.Compliance.CALORIES_UNDER,
                        lang,
                        actual=actual_calories,
                        planned=planned_calories,
                        percent=round((1 - calorie_ratio) * 100)
                    ))

            # Анализ БЖУ, если информация доступна
            nutrient_names = {
                'proteins': self.get_localized_message(LK.Tracking.Compliance.PROTEINS, lang),
                'fats': self.get_localized_message(LK.Tracking.Compliance.FATS, lang),
                'carbs': self.get_localized_message(LK.Tracking.Compliance.CARBS, lang)
            }

            bju_imbalance = []

            for nutrient, name in nutrient_names.items():
                if nutrient in nutrients_consumed and nutrient in planned_meal:
                    planned = planned_meal[nutrient]
                    actual = nutrients_consumed[nutrient]

                    if planned > 0:
                        ratio = actual / planned

                        if ratio > 1.3:
                            bju_imbalance.append(f"{name} (+{round((ratio - 1) * 100)}%)")
                        elif ratio < 0.7:
                            bju_imbalance.append(f"{name} (-{round((1 - ratio) * 100)}%)")

            # Добавляем рекомендацию по балансу БЖУ
            if bju_imbalance:
                recommendations.append(self.get_localized_message(
                    LK.Tracking.Compliance.MACROS_IMBALANCE,
                    lang,
                    imbalances=", ".join(bju_imbalance)
                ))

            # Формируем итоговую рекомендацию
            if recommendations:
                return "\n".join(recommendations)
            return ""

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return ""

    def get_error_message(self, lang: str) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Commands.Compliance.INVALID_FORMAT, lang)
