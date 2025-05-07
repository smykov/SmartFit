from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import date
from app.models.tracking import (
    WeightGoalProgress,
    DailyTrackingStatus,
    MealComplianceStatus
)


class ITrackingService(ABC):
    """
    Интерфейс сервиса для трекинга прогресса пользователя
    """

    @abstractmethod
    async def record_weight(self, user_id: str, weight: float, notes: str = None) -> bool:
        """
        Записывает вес пользователя

        Args:
            user_id: ID пользователя
            weight: Вес в кг
            notes: Дополнительные заметки

        Returns:
            bool: Результат операции
        """
        pass

    @abstractmethod
    async def record_water_intake(self, user_id: str, amount: float) -> bool:
        """
        Записывает потребление воды

        Args:
            user_id: ID пользователя
            amount: Количество воды в мл

        Returns:
            bool: Результат операции
        """
        pass

    @abstractmethod
    async def record_meal_compliance(
            self,
            user_id: str,
            date_val: date,
            meal_type: str,
            status: MealComplianceStatus,
            notes: str = None,
            alternative_meal: str = None,
            nutrients_consumed: Dict[str, float] = None
    ) -> bool:
        """
        Записывает соблюдение режима питания с расширенными данными

        Args:
            user_id: ID пользователя
            date_val: Дата
            meal_type: Тип приема пищи
            status: Статус соблюдения
            notes: Дополнительные заметки (отчет пользователя)
            alternative_meal: Альтернативное блюдо
            nutrients_consumed: Словарь с данными о потреблённых нутриентах
                {
                    "calories": float,
                    "proteins": float,
                    "fats": float,
                    "carbs": float
                }

        Returns:
            bool: Результат операции
        """
        pass

    @abstractmethod
    async def calculate_weight_progress(self, user_id: str) -> Optional[WeightGoalProgress]:
        """
        Рассчитывает прогресс в достижении цели по весу

        Args:
            user_id: ID пользователя

        Returns:
            Optional[WeightGoalProgress]: Прогресс или None
        """
        pass

    @abstractmethod
    async def get_daily_status(self, user_id: str) -> Optional[DailyTrackingStatus]:
        """
        Получает статус трекинга на сегодняшний день

        Args:
            user_id: ID пользователя

        Returns:
            Optional[DailyTrackingStatus]: Статус трекинга или None
        """
        pass

    @abstractmethod
    async def get_diet_compliance(
            self,
            user_id: str,
            date_val: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Получает статистику соблюдения плана питания

        Args:
            user_id: ID пользователя
            date_val: Дата (если None, используется текущая дата)

        Returns:
            Optional[Dict[str, Any]]: Статистика соблюдения или None
        """
        pass

    @abstractmethod
    async def generate_weekly_report(self, user_id: str) -> Optional[str]:
        """
        Генерирует еженедельный отчет о прогрессе

        Args:
            user_id: ID пользователя

        Returns:
            Optional[str]: Текст отчета или None
        """
        pass

    @abstractmethod
    async def get_weight_history(
            self,
            user_id: str,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> Optional[Dict[str, float]]:
        """
        Получает историю веса пользователя за период

        Args:
            user_id: ID пользователя
            start_date: Начальная дата периода
            end_date: Конечная дата периода

        Returns:
            Optional[Dict[str, float]]: История веса или None
        """
        pass

    @abstractmethod
    async def get_water_history(
            self,
            user_id: str,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> Optional[Dict[str, float]]:
        """
        Получает историю потребления воды за период

        Args:
            user_id: ID пользователя
            start_date: Начальная дата периода
            end_date: Конечная дата периода

        Returns:
            Optional[Dict[str, float]]: История потребления воды или None
        """
        pass

    @abstractmethod
    async def get_compliance_by_period(self, user_id: str, start_date: date = None,
                                       end_date: date = None) -> List[Dict[str, Any]]:
        """
        Получает статистику соблюдения плана питания за период

        Args:
            user_id: ID пользователя
            start_date: Начальная дата периода
            end_date: Конечная дата периода

        Returns:
            List[Dict[str, Any]]: Список статистик соблюдения по дням
        """
        pass
