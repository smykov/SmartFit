# app/services/formatter/diet_formatter_service.py
from datetime import date
from typing import Dict, Any, List, Optional, Tuple

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.formatter.diet_formatter import DietFormatter
from app.services.formatter.shopping_list_formatter import ShoppingListFormatter
from app.services.localization.localization_interface import ILocalizationService


class DietFormatterService:
    """
    Сервис для форматирования планов диет и списков покупок.
    Использует специализированные форматтеры для разных типов контента.
    """

    def __init__(self, localization_service: ILocalizationService):
        """
        Инициализация сервиса форматирования диет

        Args:
            localization_service: Сервис локализации сообщений
        """
        self.localization_service = localization_service
        self.diet_formatter = DietFormatter(localization_service)
        self.shopping_list_formatter = ShoppingListFormatter(localization_service)
        self.logger = self.diet_formatter.logger

    def get_diet_summary(self, diet_plan: Dict[str, Any], lang: Optional[str] = None) -> str:
        """
        Создает сводку плана диеты и сообщение с командами

        Args:
            diet_plan: План диеты
            lang: Код языка

        Returns:
            Tuple[str, str]: (сводка плана, команды для взаимодействия)
        """
        return self.diet_formatter.get_diet_summary(diet_plan, lang)

    def get_diet_summary_commands(self, diet_plan: Dict[str, Any], lang: Optional[str] = None) -> str:
        """
        Создает сводку плана диеты и сообщение с командами

        Args:
            diet_plan: План диеты
            lang: Код языка

        Returns:
            str: (сводка плана, команды для взаимодействия)
        """
        return self.get_localized_message(
            LK.Diet.Full.Plan.COMMANDS_MESSAGE,
            lang
        )

    def get_full_diet_plan(self, diet_plan: Dict[str, Any], lang: Optional[str] = None) -> List[str]:
        """
        Создает полный план диеты на все дни

        Args:
            diet_plan: План диеты
            lang: Код языка

        Returns:
            List[str]: Список сообщений с планом диеты
        """
        return self.diet_formatter.get_full_diet_plan(diet_plan, lang)

    def get_day_diet_plan(self, diet_plan: Dict[str, Any], day_date: date = None, lang: Optional[str] = None) -> List[str]:
        """
        Создает детальный план диеты на конкретный день

        Args:
            diet_plan: План диеты
            day_date: Дата, на которую нужен план
            lang: Код языка

        Returns:
            List[str]: Сообщениz с планом на день
        """
        return self.diet_formatter.get_day_diet_plan(diet_plan, day_date, lang)

    def get_diet_tracking_info_message(self, lang: Optional[str] = None) -> str:
        """
        Создает сообщение с информацией о командах трекинга диеты

        Args:
            lang: Код языка

        Returns:
            str: Сообщение с информацией по трекингу
        """
        return self.diet_formatter.get_diet_tracking_info_message(lang)

    def get_short_diet_summary(self, diet_plan: Dict[str, Any], lang: Optional[str] = None) -> str:
        """
        Создает сводку краткой версии плана диеты для согласования

        Args:
            diet_plan: План диеты
            lang: Код языка

        Returns:
            str: Сводка плана
        """
        return self.diet_formatter.get_short_diet_summary(diet_plan, lang)

    def get_short_diet_next_steps(self, lang: Optional[str] = None) -> str:
        """
        Создает сообщение о следующих шагах после создания краткого плана диеты

        Args:
            lang: Код языка

        Returns:
            str: Информация о следующих шагах
        """
        return self.diet_formatter.get_short_diet_next_steps(lang)

    def format_shopping_list(self, shopping_list_data: Dict[str, Any], lang: Optional[str] = None) -> str:
        """
        Форматирует список покупок для отправки пользователю

        Args:
            shopping_list_data: Данные списка покупок
            lang: Код языка

        Returns:
            str: Отформатированный список покупок
        """
        return self.shopping_list_formatter.format_shopping_list(shopping_list_data, lang)

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
        return self.localization_service.get_message(key, lang, **params)
