# app/db/repositories/postgres/shopping_list_repository.py
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.db.interfaces.shopping_list_repository_interface import IShoppingListRepository
from app.db.postgres import PostgresClient
from app.db.repositories.postgres.base_repository import PostgresBaseRepository


class PostgresShoppingListRepository(PostgresBaseRepository, IShoppingListRepository):
    """
    Реализация репозитория списков покупок с использованием PostgreSQL
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Инициализация репозитория

        Args:
            postgres_client: Клиент PostgreSQL
        """
        super().__init__(postgres_client, "shopping_lists")
        self.json_fields = ["items"]

    async def create(self, shopping_list_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает новый список покупок

        Args:
            shopping_list_data: Данные списка покупок

        Returns:
            Optional[str]: ID созданного списка или None в случае ошибки
        """
        try:
            prepared_data = self._prepare_data(shopping_list_data)
            return await self.client.add_document(self.collection, prepared_data)
        except Exception as e:
            print(f"Error creating shopping list: {str(e)}")
            return None

    async def get_by_id(self, list_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает список покупок по ID

        Args:
            list_id: ID списка покупок

        Returns:
            Optional[Dict[str, Any]]: Данные списка покупок или None, если список не найден
        """
        try:
            shopping_list = await self.client.get_document(self.collection, list_id)
            return self._parse_data(shopping_list, self.json_fields)
        except Exception as e:
            print(f"Error getting shopping list by ID: {str(e)}")
            return None

    async def update(self, list_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные списка покупок

        Args:
            list_id: ID списка покупок
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

            return await self.client.update_document(self.collection, list_id, data_to_update)
        except Exception as e:
            print(f"Error updating shopping list: {str(e)}")
            return False

    async def delete(self, list_id: str) -> bool:
        """
        Удаляет список покупок

        Args:
            list_id: ID списка покупок

        Returns:
            bool: Результат удаления
        """
        try:
            return await self.client.delete_document(self.collection, list_id)
        except Exception as e:
            print(f"Error deleting shopping list: {str(e)}")
            return False

    async def get_by_diet_plan(self, diet_plan_id: str) -> List[Dict[str, Any]]:
        """
        Получает списки покупок для конкретного плана диеты

        Args:
            diet_plan_id: ID плана диеты

        Returns:
            List[Dict[str, Any]]: Списки покупок для указанного плана диеты
        """
        try:
            query = """
                SELECT * FROM shopping_lists
                WHERE diet_plan_id = $1
                ORDER BY created_at DESC
            """

            shopping_lists = await self.client.fetch(query, diet_plan_id)
            return [self._parse_data(shopping_list, self.json_fields) for shopping_list in shopping_lists]
        except Exception as e:
            print(f"Error getting shopping lists by diet plan: {str(e)}")
            return []

    async def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Получает списки покупок пользователя

        Args:
            user_id: ID пользователя

        Returns:
            List[Dict[str, Any]]: Списки покупок указанного пользователя
        """
        try:
            query = """
                SELECT * FROM shopping_lists
                WHERE user_id = $1
                ORDER BY created_at DESC
            """

            shopping_lists = await self.client.fetch(query, user_id)
            return [self._parse_data(shopping_list, self.json_fields) for shopping_list in shopping_lists]
        except Exception as e:
            print(f"Error getting shopping lists by user: {str(e)}")
            return []

    async def mark_item_as_purchased(self, list_id: str, item_name: str) -> bool:
        """
        Отмечает элемент списка как купленный

        Args:
            list_id: ID списка покупок
            item_name: Название продукта

        Returns:
            bool: Результат операции
        """
        try:
            # Получаем текущий список покупок
            shopping_list = await self.get_by_id(list_id)
            if not shopping_list:
                return False

            # Получаем список элементов
            items = shopping_list.get("items", [])
            item_found = False

            # Обновляем статус элемента
            for item in items:
                if item.get("name", "").lower() == item_name.lower():
                    item["is_purchased"] = True
                    item_found = True

            if not item_found:
                return False

            # Обновляем список покупок
            return await self.update(list_id, {
                "items": items,
                "updated_at": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error marking item as purchased: {str(e)}")
            return False