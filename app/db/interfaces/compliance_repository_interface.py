# app/db/interfaces/compliance_repository_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import date


class IComplianceRepository(ABC):
    """
    Интерфейс для работы с репозиторием записей соблюдения плана питания
    """

    @abstractmethod
    async def add_meal_compliance(self, user_id: str, date_value: date, meal_type: str,
                                  status: str, notes: str = None,
                                  alternative_meal: str = None) -> Optional[str]:
        """
        Добавляет запись о соблюдении приема пищи

        Args:
            user_id: ID пользователя
            date_value: Дата
            meal_type: Тип приема пищи (breakfast, lunch, dinner, snack)
            status: Статус соблюдения (followed, partially, substituted, skipped)
            notes: Дополнительные заметки
            alternative_meal: Альтернативное блюдо (если status=substituted)

        Returns:
            Optional[str]: ID созданной записи или None в случае ошибки
        """
        pass

    @abstractmethod
    async def get_daily_compliance(self, user_id: str, date_value: date) -> Optional[Dict[str, Any]]:
        """
        Получает статистику соблюдения плана питания за день

        Args:
            user_id: ID пользователя
            date_value: Дата

        Returns:
            Optional[Dict[str, Any]]: Статистика соблюдения или None
        """
        pass

    @abstractmethod
    async def update_daily_compliance(self, user_id: str, date_value: date) -> bool:
        """
        Обновляет общую статистику соблюдения плана питания за день

        Args:
            user_id: ID пользователя
            date_value: Дата

        Returns:
            bool: Результат обновления
        """
        pass

    @abstractmethod
    async def get_compliance_by_period(self, user_id: str, start_date: date,
                                       end_date: date) -> List[Dict[str, Any]]:
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

    @abstractmethod
    async def delete_compliance(self, compliance_id: str) -> bool:
        """
        Удаляет запись о соблюдении плана питания

        Args:
            compliance_id: ID записи

        Returns:
            bool: Результат удаления
        """
        pass