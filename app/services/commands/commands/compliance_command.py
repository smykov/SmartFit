# app/services/commands/commands/compliance_command.py
import re
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

        # Маппинги будут заполнены в методе execute при первом вызове
        self._status_keywords = None
        self._meal_type_keywords = None
        self._meal_type_display = None

    def _init_mappings(self, lang: str = "en"):
        """
        Инициализирует маппинги из языковых модулей

        Args:
            lang: Код языка пользователя (для записи в логи)
        """
        if self._status_keywords is not None:
            # Маппинги уже инициализированы
            return

        self.logger.info(f"Initializing compliance mappings (user language: {lang})")

        # Инициализируем пустые маппинги
        self._status_keywords = {}
        self._meal_type_keywords = {}
        self._meal_type_display = {}

        # Загружаем маппинги из всех языковых модулей
        for language_code in ["en", "ru", "es"]:
            try:
                # Получаем маппинги статусов из локализационных модулей
                status_keywords_str = self.get_localized_message("commands.compliance.statusKeywords", language_code)
                if status_keywords_str and not status_keywords_str.startswith("commands.compliance"):
                    # Конвертируем строковое представление в словарь
                    try:
                        status_keywords = eval(status_keywords_str)
                        for key, value in status_keywords.items():
                            # Преобразуем строковые значения в константы MealComplianceStatus
                            if value == 'followed':
                                status_value = MealComplianceStatus.FOLLOWED
                            elif value == 'partially':
                                status_value = MealComplianceStatus.PARTIALLY
                            elif value == 'substituted':
                                status_value = MealComplianceStatus.SUBSTITUTED
                            elif value == 'skipped':
                                status_value = MealComplianceStatus.SKIPPED
                            else:
                                status_value = value

                            self._status_keywords[key] = status_value
                    except Exception as e:
                        self.logger.error(f"Error parsing status keywords for language {language_code}: {e}")

                # Получаем маппинги типов приема пищи из локализационных модулей
                meal_type_keywords_str = self.get_localized_message("commands.compliance.mealTypeKeywords",
                                                                    language_code)
                if meal_type_keywords_str and not meal_type_keywords_str.startswith("commands.compliance"):
                    try:
                        meal_type_keywords = eval(meal_type_keywords_str)
                        self._meal_type_keywords.update(meal_type_keywords)
                    except Exception as e:
                        self.logger.error(f"Error parsing meal type keywords for language {language_code}: {e}")

                # Получаем маппинги отображения типов приема пищи
                meal_type_display_str = self.get_localized_message("commands.compliance.mealTypeDisplay", language_code)
                if meal_type_display_str and not meal_type_display_str.startswith("commands.compliance"):
                    try:
                        meal_type_display = eval(meal_type_display_str)
                        if language_code not in self._meal_type_display:
                            self._meal_type_display[language_code] = {}
                        self._meal_type_display[language_code].update(meal_type_display)
                    except Exception as e:
                        self.logger.error(f"Error parsing meal type display for language {language_code}: {e}")
            except Exception as e:
                self.logger.error(f"Error loading mappings for language {language_code}: {e}")

        # Если не удалось загрузить маппинги из локализационных модулей, используем дефолтные
        if not self._status_keywords:
            self.logger.warning("Using default status keywords mapping")
            self._status_keywords = {
                # Английские ключевые слова
                "completed": MealComplianceStatus.FOLLOWED,
                "followed": MealComplianceStatus.FOLLOWED,
                "partially": MealComplianceStatus.PARTIALLY,
                "substituted": MealComplianceStatus.SUBSTITUTED,
                "skipped": MealComplianceStatus.SKIPPED,

                # Русские ключевые слова
                "выполнено": MealComplianceStatus.FOLLOWED,
                "частично": MealComplianceStatus.PARTIALLY,
                "заменил": MealComplianceStatus.SUBSTITUTED,
                "пропустил": MealComplianceStatus.SKIPPED,

                # Испанские ключевые слова
                "completado": MealComplianceStatus.FOLLOWED,
                "parcial": MealComplianceStatus.PARTIALLY,
                "sustituido": MealComplianceStatus.SUBSTITUTED,
                "omitido": MealComplianceStatus.SKIPPED
            }

        if not self._meal_type_keywords:
            self.logger.warning("Using default meal type keywords mapping")
            self._meal_type_keywords = {
                # Английские ключевые слова
                "breakfast": "breakfast",
                "lunch": "lunch",
                "dinner": "dinner",
                "snack": "snack",

                # Русские ключевые слова
                "завтрак": "breakfast",
                "обед": "lunch",
                "ужин": "dinner",
                "перекус": "snack",

                # Испанские ключевые слова
                "desayuno": "breakfast",
                "almuerzo": "lunch",
                "cena": "dinner",
                "merienda": "snack"
            }

        if not self._meal_type_display:
            self.logger.warning("Using default meal type display mapping")
            self._meal_type_display = {
                "en": {"breakfast": "breakfast", "lunch": "lunch", "dinner": "dinner", "snack": "snack"},
                "ru": {"breakfast": "завтрак", "lunch": "обед", "dinner": "ужин", "snack": "перекус"},
                "es": {"breakfast": "desayuno", "lunch": "almuerzo", "dinner": "cena", "snack": "merienda"}
            }

        self.logger.info(f"Mappings initialized: {len(self._status_keywords)} status keywords, " +
                         f"{len(self._meal_type_keywords)} meal type keywords, " +
                         f"{len(self._meal_type_display)} languages for display")

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

            # Инициализируем маппинги из языковых модулей при первом вызове
            self._init_mappings(lang)

            self.logger.info(f"Processing compliance command: params: {params}")

            # Проверяем наличие параметров
            if not params or 'params' not in params:
                self.logger.error("Error recording compliance: no parameters provided")
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.INVALID_FORMAT, lang)
                }

            # Получаем текст сообщения и выполняем предварительную очистку
            if len(params['params']) < 2:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.INVALID_FORMAT, lang)
                }

            status_text = params['params'][0].lower().strip()
            meal_type_text = params['params'][1].lower().strip()

            # Определяем статус из любого языка
            status = self._status_keywords.get(status_text)
            if not status:
                self.logger.error(
                    f"Error recording compliance: Unknown compliance type '{status_text}'")
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.INVALID_TYPE, lang)
                }

            # Определяем тип приема пищи из любого языка
            meal_type = self._meal_type_keywords.get(meal_type_text)
            if not meal_type:
                self.logger.error(f"Error recording compliance: Unknown meal type '{meal_type_text}'")
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.INVALID_MEAL_TYPE, lang)
                }

            # Получаем текущую дату
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Проверяем наличие плана диеты
            diet_plan = await self.dependencies['diet_service'].get_current_diet(user_id)

            if not diet_plan:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Compliance.NO_DIET_PLAN, lang)
                }

            self.logger.info(f"Recording compliance: type={meal_type}, status={status}")

            try:
                # Записываем соблюдение через трекинг-сервис
                result = await self.dependencies['tracking_service'].record_meal_compliance(
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
                compliance_data = await self.dependencies['tracking_service'].get_diet_compliance(user_id, today)

                # Получаем локализованное отображение типа приема пищи
                meal_type_display = meal_type
                if lang in self._meal_type_display and meal_type in self._meal_type_display[lang]:
                    meal_type_display = self._meal_type_display[lang][meal_type]

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
                    # Если форматтер недоступен, используем простое сообщение
                    message = self.get_localized_message(
                        LK.Commands.Compliance.RECORDED,
                        lang,
                        meal_type=meal_type_display,
                        status=status_text
                    )

                return {
                    "success": True,
                    "message": message
                }

            except Exception as e:
                self.logger.error(f"Error recording compliance: {str(e)}")
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
