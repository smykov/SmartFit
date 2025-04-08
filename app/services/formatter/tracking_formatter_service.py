# app/services/formatter/tracking_formatter_service.py
from typing import Dict, Any, Optional

from app.services.formatter.tracking_formatter import TrackingFormatter
from app.services.localization.localization_interface import ILocalizationService


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

    def format_weight_recorded_message(self, weight: float, progress: Optional[Dict[str, Any]] = None, 
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
        return self.tracking_formatter.format_weight_recorded_message(weight, progress, lang)
        
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
        
    def format_stats_message(self, weight_progress: Optional[Dict[str, Any]], 
                            today_status: Optional[Dict[str, Any]], 
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
        return self.tracking_formatter.format_stats_message(weight_progress, today_status, compliance_data, lang)
