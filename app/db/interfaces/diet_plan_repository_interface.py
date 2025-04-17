# app/db/interfaces/diet_plan_repository_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import date


class IDietPlanRepository(ABC):
    """
    Интерфейс для работы с репозиторием планов диет
    """

    @abstractmethod
    async def create(self, diet_plan_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает новый план диеты

        Args:
            diet_plan_data: Данные плана диеты

        Returns:
            Optional[str]: ID созданного плана или None в случае ошибки
        """
        pass

    @abstractmethod
    async def get_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты по ID

        Args:
            plan_id: ID плана диеты

        Returns:
            Optional[Dict[str, Any]]: Данные плана диеты или None, если план не найден
        """
        pass

    @abstractmethod
    async def update(self, plan_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные плана диеты

        Args:
            plan_id: ID плана диеты
            update_data: Данные для обновления

        Returns:
            bool: Результат обновления
        """
        pass

    @abstractmethod
    async def delete(self, plan_id: str) -> bool:
        """
        Удаляет план диеты

        Args:
            plan_id: ID плана диеты

        Returns:
            bool: Результат удаления
        """
        pass

    @abstractmethod
    async def get_current_diet(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает текущий активный план диеты пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Текущий план диеты или None
        """
        pass

    @abstractmethod
    async def get_user_plans(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Получает все планы пользователя

        Args:
            user_id: ID пользователя

        Returns:
            List[Dict[str, Any]]: Список планов пользователя
        """
        pass

    @abstractmethod
    async def update_daily_plan(self, plan_id: str, day_key: str, day_data: Dict[str, Any]) -> bool:
        """
        Обновляет план на конкретный день

        Args:
            plan_id: ID плана диеты
            day_key: Ключ дня (дата или день недели)
            day_data: Данные дня для обновления

        Returns:
            bool: Результат обновления
        """
        pass

    @abstractmethod
    async def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Находит планы диет по статусу

        Args:
            status: Статус планов для поиска

        Returns:
            List[Dict[str, Any]]: Список планов с указанным статусом
        """
        pass