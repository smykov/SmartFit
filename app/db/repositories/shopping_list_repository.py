# app/db/repositories/shopping_list_repository.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pytz

from app.db.firebase import firebase_client
from app.db.interfaces.shopping_list_repository_interface import IShoppingListRepository
from config import settings

logger = logging.getLogger(__name__)


class FirebaseShoppingListRepository(IShoppingListRepository):
    """
    Репозиторий для работы со списками покупок через Firebase
    """

    async def create(self, shopping_list_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает новый список покупок

        Args:
            shopping_list_data: Данные списка покупок

        Returns:
            Optional[str]: ID созданного списка или None в случае ошибки
        """
        try:
            now = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            if 'created_at' not in shopping_list_data:
                shopping_list_data['created_at'] = now
            shopping_list_data['updated_at'] = now

            list_id = firebase_client.add_document("shopping_lists", shopping_list_data)

            if not list_id:
                logger.error("Failed to create shopping list")
                return None

            return list_id
        except Exception as e:
            logger.error(f"Error creating shopping list: {str(e)}")
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
            shopping_list = firebase_client.get_document("shopping_lists", list_id)
            return shopping_list
        except Exception as e:
            logger.error(f"Error getting shopping list by ID: {str(e)}")
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
            update_data['updated_at'] = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()

            result = firebase_client.update_document("shopping_lists", list_id, update_data)
            return result
        except Exception as e:
            logger.error(f"Error updating shopping list: {str(e)}")
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
            result = firebase_client.delete_document("shopping_lists", list_id)
            return result
        except Exception as e:
            logger.error(f"Error deleting shopping list: {str(e)}")
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
            shopping_lists = firebase_client.query_documents(
                "shopping_lists",
                "diet_plan_id",
                "==",
                diet_plan_id
            )
            return shopping_lists
        except Exception as e:
            logger.error(f"Error getting shopping lists by diet plan: {str(e)}")
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
            shopping_lists = firebase_client.query_documents(
                "shopping_lists",
                "user_id",
                "==",
                user_id
            )
            return shopping_lists
        except Exception as e:
            logger.error(f"Error getting shopping lists by user: {str(e)}")
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
            # Получаем текущий список
            shopping_list = await self.get_by_id(list_id)

            if not shopping_list or "items" not in shopping_list:
                logger.error(f"Shopping list {list_id} not found or has no items")
                return False

            # Ищем продукт по имени (без учета регистра)
            item_name_lower = item_name.lower()
            found = False
            updated_items = []

            for item in shopping_list["items"]:
                current_item = item.copy()  # Копируем для безопасности
                if item_name_lower in current_item.get("name", "").lower():
                    current_item["is_purchased"] = True
                    found = True
                updated_items.append(current_item)

            if not found:
                logger.warning(f"Item {item_name} not found in shopping list {list_id}")
                return False

            # Обновляем список
            result = await self.update(list_id, {"items": updated_items})
            return result

        except Exception as e:
            logger.error(f"Error marking item as purchased: {str(e)}")
            return False