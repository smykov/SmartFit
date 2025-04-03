# app/services/diet/shopping_list_manager.py

from typing import Dict, Any
from datetime import datetime
import pytz
import json

from app.localization.messages import DietMessages
from app.services.diet.base_service import BaseDietService
from app.db.firebase import firebase_client
from app.templates.prompts import create_shopping_list_system_prompt, create_shopping_list_user_prompt
from config import settings


class ShoppingListManager(BaseDietService):
    """Класс для управления списками покупок"""

    def __init__(self, llm_service):
        """
        Инициализация менеджера списков покупок

        Args:
            llm_service: Сервис LLM для генерации списков покупок
        """
        super().__init__()
        self.llm_service = llm_service
        self.messages = DietMessages()

    async def generate_shopping_list(self, diet_plan_id: str) -> Dict[str, Any]:
        """
        Создает список покупок на основе плана диеты

        Args:
            diet_plan_id: ID плана диеты

        Returns:
            Dict[str, Any]: Список покупок или словарь с ошибкой
        """
        try:
            # Получаем план диеты
            diet_plan = firebase_client.get_document("diet_plans", diet_plan_id)

            if not diet_plan:
                self.logger.error(f"Diet plan {diet_plan_id} not found")
                return {"error": "Diet plan not found"}

            # Проверяем наличие существующего списка покупок для этого плана
            existing_lists = firebase_client.query_documents("shopping_lists", "diet_plan_id", "==", diet_plan_id)

            # Находим самый последний список покупок
            if existing_lists:
                latest_list = max(existing_lists, key=lambda x: x.get("created_at", ""))

                # Проверяем, не было ли изменений в плане диеты с момента создания списка покупок
                list_timestamp = datetime.fromisoformat(latest_list.get("created_at", "2000-01-01T00:00:00"))

                # Проверяем наличие изменений в плане
                modifications_history = diet_plan.get("modifications_history", [])

                # Если нет истории изменений или последнее изменение было до создания списка покупок,
                # возвращаем существующий список
                if not modifications_history or all(
                        datetime.fromisoformat(mod.get("timestamp", "2000-01-01T00:00:00")) < list_timestamp
                        for mod in modifications_history
                ):
                    self.logger.info(f"Using existing shopping list for diet plan {diet_plan_id}")
                    return latest_list

            # Генерируем промпты для списка покупок
            system_prompt = create_shopping_list_system_prompt()
            user_prompt = create_shopping_list_user_prompt(diet_plan)

            # Генерируем список покупок через LLM
            response = await self.llm_service.generate_completion(system_prompt, user_prompt)

            try:
                # Парсим JSON-ответ
                shopping_list = json.loads(response)
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse JSON response for shopping list: {response}")
                return {"error": "Failed to parse shopping list response"}

            # Если был найден предыдущий список покупок, переносим информацию о покупках в новый список
            if existing_lists:
                latest_list = max(existing_lists, key=lambda x: x.get("created_at", ""))

                # Создаем словарь покупок из предыдущего списка
                purchased_items = {}
                for item in latest_list.get("items", []):
                    if item.get("is_purchased", False):
                        purchased_items[item.get("name", "").lower()] = True

                # Переносим статус покупки в новый список
                for item in shopping_list:
                    item_name = item.get("name", "").lower()
                    if item_name in purchased_items:
                        item["is_purchased"] = True

            # Вычисляем общую стоимость
            total_estimated_price = sum(
                [item.get("estimated_price", 0) for item in shopping_list if item.get("estimated_price")]
            )

            # Сохраняем список покупок
            shopping_list_data = {
                "user_id": diet_plan.get("user_id"),
                "diet_plan_id": diet_plan_id,
                "items": shopping_list,
                "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                "total_estimated_price": total_estimated_price
            }

            list_id = firebase_client.add_document("shopping_lists", shopping_list_data)

            if not list_id:
                self.logger.error("Failed to save shopping list to database")
                return {"error": "Failed to save shopping list"}

            # Добавляем ID в список
            shopping_list_data["id"] = list_id

            return shopping_list_data

        except Exception as e:
            self.logger.error(f"Error generating shopping list: {str(e)}")
            return {"error": str(e)}

    async def mark_product_as_purchased(self, user_id: str, product_name: str) -> Dict[str, Any]:
        """
        Отмечает продукт как купленный в списке покупок

        Args:
            user_id: ID пользователя
            product_name: Название продукта

        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            # Получаем текущий план диеты пользователя
            diet_plans = firebase_client.query_documents("diet_plans", "user_id", "==", user_id)
            if not diet_plans:
                return {"success": False, "message": self.messages.NO_DIET_PLAN}

            # Берем самый последний план
            current_plan = max(diet_plans, key=lambda p: p.get("created_at", ""))

            # Получаем список покупок для текущего плана
            shopping_lists = firebase_client.query_documents(
                "shopping_lists",
                "diet_plan_id",
                "==",
                current_plan["id"]
            )

            if not shopping_lists:
                return {"success": False, "message": self.messages.NO_SHOPPING_LIST}

            # Берем последний список покупок
            shopping_list = shopping_lists[0]

            # Найдем продукт в списке (нечеткий поиск)
            found = False
            updated_items = []

            for item in shopping_list.get("items", []):
                item_name = item.get("name", "").lower()
                if product_name.lower() in item_name or item_name in product_name.lower():
                    # Отмечаем продукт как купленный
                    item["is_purchased"] = True
                    found = True

                updated_items.append(item)

            if found:
                # Обновляем список покупок
                firebase_client.update_document(
                    "shopping_lists",
                    shopping_list["id"],
                    {
                        "items": updated_items,
                        "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
                    }
                )

                return {
                    "success": True,
                    "message": self.messages.PRODUCT_MARKED.format(product=product_name)
                }
            else:
                return {
                    "success": False,
                    "message": self.messages.PRODUCT_NOT_FOUND.format(product=product_name)
                }

        except Exception as e:
            self.logger.error(f"Error marking product as purchased: {str(e)}")
            return {"success": False, "error": str(e)}