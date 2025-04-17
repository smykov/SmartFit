# app/db/repositories/postgres_product_repository.py
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.db.interfaces.product_repository_interface import IProductRepository
from app.db.postgres import PostgresClient
from app.db.repositories.postgres.base_repository import PostgresBaseRepository

class PostgresProductRepository(PostgresBaseRepository, IProductRepository):
    """
    Реализация репозитория продуктов с использованием PostgreSQL
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Инициализация репозитория

        Args:
            postgres_client: Клиент PostgreSQL
        """
        super().__init__(postgres_client, "products")
        self.json_fields = ["nutrition", "store_prices", "seasonal_months", "regions", "tags"]

    async def create(self, product_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает новый продукт

        Args:
            product_data: Данные продукта

        Returns:
            Optional[str]: ID созданного продукта или None в случае ошибки
        """
        try:
            prepared_data = self._prepare_data(product_data)
            return await self.client.add_document(self.collection, prepared_data)
        except Exception as e:
            print(f"Error creating product: {str(e)}")
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
            product = await self.client.get_document(self.collection, product_id)
            return self._parse_data(product, self.json_fields)
        except Exception as e:
            print(f"Error getting product by ID: {str(e)}")
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
            update_data["updated_at"] = datetime.now().isoformat()
            data_to_update = {}

            for key, value in update_data.items():
                if isinstance(value, (dict, list)):
                    data_to_update[key] = json.dumps(value)
                else:
                    data_to_update[key] = value

            return await self.client.update_document(self.collection, product_id, data_to_update)
        except Exception as e:
            print(f"Error updating product: {str(e)}")
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
            return await self.client.delete_document(self.collection, product_id)
        except Exception as e:
            print(f"Error deleting product: {str(e)}")
            return False

    async def get_all(self) -> List[Dict[str, Any]]:
        """
        Получает все продукты

        Returns:
            List[Dict[str, Any]]: Список продуктов
        """
        try:
            products = await self.client.get_all_documents(self.collection)
            return [self._parse_data(product, self.json_fields) for product in products]
        except Exception as e:
            print(f"Error getting all products: {str(e)}")
            return []

    async def search_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Ищет продукты по имени

        Args:
            name: Название продукта (или его часть)

        Returns:
            List[Dict[str, Any]]: Список найденных продуктов
        """
        try:
            query = """
                SELECT * FROM products
                WHERE name ILIKE $1 OR local_name ILIKE $1
                ORDER BY name
            """

            products = await self.client.fetch(query, f"%{name}%")
            return [self._parse_data(product, self.json_fields) for product in products]
        except Exception as e:
            print(f"Error searching products by name: {str(e)}")
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
            query = """
                SELECT * FROM products
                WHERE category = $1
                ORDER BY name
            """

            products = await self.client.fetch(query, category)
            return [self._parse_data(product, self.json_fields) for product in products]
        except Exception as e:
            print(f"Error getting products by category: {str(e)}")
            return []