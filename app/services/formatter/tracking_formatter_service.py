# app/services/formatter/tracking_formatter_service.py
from typing import Dict, Any, Optional

from app.models.tracking import WeightGoalProgress, DailyTrackingStatus
from app.services.formatter.tracking_formatter import TrackingFormatter
from app.services.localization.localization_interface import ILocalizationService
from app.utils.format_helper import FormatHelper


class TrackingFormatterService:
    """
    Сервис для форматирования данных трекинга
    """

    def __init__(self, localization_service: ILocalizationService):
        """
        Инициализация сервиса форматирования трекинга

        Args:
            localization_service: Сервис локализации сообщений
        """
        self.localization_service = localization_service
        self.tracking_formatter = TrackingFormatter(localization_service)
        self.logger = self.tracking_formatter.logger

    def format_weight_recorded_message(self, weight: float, progress: Optional[WeightGoalProgress] = None,
                                       lang: Optional[str] = None) -> str:
        """
        Форматирует сообщение о записи веса

        Args:
            weight: Записанный вес
            progress: Информация о прогрессе
            lang: Код языка

        Returns:
            str: Отформатированное сообщение
        """
        # Преобразуем объект прогресса в словарь
        progress_dict = self._convert_to_dict(progress)
        return self.tracking_formatter.format_weight_recorded_message(weight, progress_dict, lang)

    def format_water_recorded_message(self, amount: float, ml_amount: float,
                                      status: Optional[Dict[str, Any]] = None,
                                      lang: Optional[str] = None) -> str:
        """
        Форматирует сообщение о записи потребления воды

        Args:
            amount: Количество стаканов
            ml_amount: Количество в миллилитрах
            status: Статус трекинга
            lang: Код языка

        Returns:
            str: Отформатированное сообщение
        """
        return self.tracking_formatter.format_water_recorded_message(amount, ml_amount, status, lang)

    def format_compliance_message(self, meal_type: str, status: str,
                                  compliance_data: Optional[Dict[str, Any]] = None,
                                  lang: Optional[str] = None) -> str:
        """
        Форматирует сообщение о соблюдении режима питания

        Args:
            meal_type: Тип приема пищи
            status: Статус соблюдения
            compliance_data: Общие данные о соблюдении
            lang: Код языка

        Returns:
            str: Отформатированное сообщение
        """
        return self.tracking_formatter.format_compliance_message(meal_type, status, compliance_data, lang)

    def format_stats_message(self, weight_progress: Optional[WeightGoalProgress],
                             today_status: Optional[DailyTrackingStatus],
                             compliance_data: Optional[Dict[str, Any]],
                             lang: Optional[str] = None) -> str:
        """
        Форматирует сообщение со статистикой

        Args:
            weight_progress: Прогресс по весу
            today_status: Статус трекинга на сегодня
            compliance_data: Данные о соблюдении плана
            lang: Код языка

        Returns:
            str: Отформатированное сообщение
        """
        # Преобразуем объекты прогресса в словарь
        weight_progress_dict = self._convert_to_dict(weight_progress)
        today_status_dict = self._convert_to_dict(today_status)

        return self.tracking_formatter.format_stats_message(weight_progress_dict, today_status_dict, compliance_data, lang)

    def _convert_to_dict(self, obj: Any) -> Dict[str, Any]:
        return FormatHelper.convert_to_dict(obj)

