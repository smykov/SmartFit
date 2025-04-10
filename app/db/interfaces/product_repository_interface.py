# app/db/interfaces/product_repository_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IProductRepository(ABC):
    """
    Интерфейс для работы с репозиторием продуктов
    """

    @abstractmethod
    async def create(self, product_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает новый продукт

        Args:
            product_data: Данные продукта

        Returns:
            Optional[str]: ID созданного продукта или None в случае ошибки
        """
        pass

    @abstractmethod
    async def get_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает продукт по ID

        Args:
            product_id: ID продукта

        Returns:
            Optional[Dict[str, Any]]: Данные продукта или None, если продукт не найден
        """
        pass

    @abstractmethod
    async def update(self, product_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные продукта

        Args:
            product_id: ID продукта
            update_data: Данные для обновления

        Returns:
            bool: Результат обновления
        """
        pass

    @abstractmethod
    async def delete(self, product_id: str) -> bool:
        """
        Удаляет продукт

        Args:
            product_id: ID продукта

        Returns:
            bool: Результат удаления
        """
        pass

    @abstractmethod
    async def get_all(self) -> List[Dict[str, Any]]:
        """
        Получает все продукты

        Returns:
            List[Dict[str, Any]]: Список продуктов
        """
        pass

    @abstractmethod
    async def search_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Ищет продукты по имени

        Args:
            name: Название продукта (или его часть)

        Returns:
            List[Dict[str, Any]]: Список найденных продуктов
        """
        pass

    @abstractmethod
    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Получает продукты определенной категории

        Args:
            category: Категория продукта

        Returns:
            List[Dict[str, Any]]: Список продуктов указанной категории
        """
        pass