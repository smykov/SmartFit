# app/db/interfaces/shopping_list_repository_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IShoppingListRepository(ABC):
    """
    Интерфейс для работы с репозиторием списков покупок
    """

    @abstractmethod
    async def create(self, shopping_list_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает новый список покупок

        Args:
            shopping_list_data: Данные списка покупок

        Returns:
            Optional[str]: ID созданного списка или None в случае ошибки
        """
        pass

    @abstractmethod
    async def get_by_id(self, list_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает список покупок по ID

        Args:
            list_id: ID списка покупок

        Returns:
            Optional[Dict[str, Any]]: Данные списка покупок или None, если список не найден
        """
        pass

    @abstractmethod
    async def update(self, list_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные списка покупок

        Args:
            list_id: ID списка покупок
            update_data: Данные для обновления

        Returns:
            bool: Результат обновления
        """
        pass

    @abstractmethod
    async def delete(self, list_id: str) -> bool:
        """
        Удаляет список покупок

        Args:
            list_id: ID списка покупок

        Returns:
            bool: Результат удаления
        """
        pass

    @abstractmethod
    async def get_by_diet_plan(self, diet_plan_id: str) -> List[Dict[str, Any]]:
        """
        Получает списки покупок для конкретного плана диеты

        Args:
            diet_plan_id: ID плана диеты

        Returns:
            List[Dict[str, Any]]: Списки покупок для указанного плана диеты
        """
        pass

    @abstractmethod
    async def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Получает списки покупок пользователя

        Args:
            user_id: ID пользователя

        Returns:
            List[Dict[str, Any]]: Списки покупок указанного пользователя
        """
        pass

    @abstractmethod
    async def mark_item_as_purchased(self, list_id: str, item_name: str) -> bool:
        """
        Отмечает элемент списка как купленный

        Args:
            list_id: ID списка покупок
            item_name: Название продукта

        Returns:
            bool: Результат операции
        """
        pass