# app/db/repositories/product_repository.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pytz

from app.db.interfaces.product_repository_interface import IProductRepository
from config import settings

logger = logging.getLogger(__name__)


class FirebaseProductRepository(IProductRepository):
    """
    Репозиторий для работы с продуктами через Firebase
    """

    def __init__(self, firebase_client):
        """
        Инициализация репозитория продуктов

        Args:
            firebase_client: Клиент Firebase для работы с базой данных
        """
        self.firebase_client = firebase_client

    async def create(self, product_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает новый продукт

        Args:
            product_data: Данные продукта

        Returns:
            Optional[str]: ID созданного продукта или None в случае ошибки
        """
        try:
            now = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            if 'created_at' not in product_data:
                product_data['created_at'] = now
            product_data['updated_at'] = now

            product_id = await self.firebase_client.add_document("products", product_data)

            if not product_id:
                logger.error("Failed to create product")
                return None

            return product_id
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            return None

    async def get_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает продукт по ID

        Args:
            product_id: ID продукта

        Returns:
            Optional[Dict[str, Any]]: Данные продукта или None, если продукт не найден
        """
        try:
            product = await self.firebase_client.get_document("products", product_id)
            return product
        except Exception as e:
            logger.error(f"Error getting product by ID: {str(e)}")
            return None

    async def update(self, product_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные продукта

        Args:
            product_id: ID продукта
            update_data: Данные для обновления

        Returns:
            bool: Результат обновления
        """
        try:
            update_data['updated_at'] = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()

            result = await self.firebase_client.update_document("products", product_id, update_data)
            return result
        except Exception as e:
            logger.error(f"Error updating product: {str(e)}")
            return False

    async def delete(self, product_id: str) -> bool:
        """
        Удаляет продукт

        Args:
            product_id: ID продукта

        Returns:
            bool: Результат удаления
        """
        try:
            result = await self.firebase_client.delete_document("products", product_id)
            return result
        except Exception as e:
            logger.error(f"Error deleting product: {str(e)}")
            return False

    async def get_all(self) -> List[Dict[str, Any]]:
        """
        Получает все продукты

        Returns:
            List[Dict[str, Any]]: Список продуктов
        """
        try:
            products = await self.firebase_client.get_all_documents("products")
            return products
        except Exception as e:
            logger.error(f"Error getting all products: {str(e)}")
            return []

    async def search_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Ищет продукты по имени (включая нечеткий поиск)

        Args:
            name: Название продукта (или его часть)

        Returns:
            List[Dict[str, Any]]: Список найденных продуктов
        """
        try:
            # В Firebase нет прямой поддержки нечеткого поиска,
            # поэтому получаем все продукты и фильтруем их в коде
            products = await self.get_all()

            # Преобразуем строку поиска в нижний регистр
            search_term = name.lower()

            # Фильтруем продукты, содержащие строку поиска в имени
            filtered_products = [
                product for product in products
                if search_term in product.get("name", "").lower() or
                   (product.get("local_name") and search_term in product.get("local_name", "").lower())
            ]

            return filtered_products

        except Exception as e:
            logger.error(f"Error searching products by name: {str(e)}")
            return []

    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Получает продукты определенной категории

        Args:
            category: Категория продукта

        Returns:
            List[Dict[str, Any]]: Список продуктов указанной категории
        """
        try:
            products = await self.firebase_client.query_documents("products", "category", "==", category)
            return products
        except Exception as e:
            logger.error(f"Error getting products by category: {str(e)}")
            return []
