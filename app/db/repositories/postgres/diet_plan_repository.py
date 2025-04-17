# app/db/repositories/postgres_diet_plan_repository.py
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.db.interfaces.diet_plan_repository_interface import IDietPlanRepository
from app.db.postgres import PostgresClient
from app.db.repositories.postgres.base_repository import PostgresBaseRepository


class PostgresDietPlanRepository(PostgresBaseRepository, IDietPlanRepository):
    """
    Реализация репозитория планов диет с использованием PostgreSQL
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Инициализация репозитория

        Args:
            postgres_client: Клиент PostgreSQL
        """
        super().__init__(postgres_client, "diet_plans")
        self.json_fields = ["daily_plans", "modifications_history"]

    async def create(self, diet_plan_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает новый план диеты

        Args:
            diet_plan_data: Данные плана диеты

        Returns:
            Optional[str]: ID созданного плана или None в случае ошибки
        """
        try:
            prepared_data = self._prepare_data(diet_plan_data)
            return await self.client.add_document(self.collection, prepared_data)
        except Exception as e:
            print(f"Error creating diet plan: {str(e)}")
            return None

    async def get_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты по ID

        Args:
            plan_id: ID плана диеты

        Returns:
            Optional[Dict[str, Any]]: Данные плана диеты или None, если план не найден
        """
        try:
            plan = await self.client.get_document(self.collection, plan_id)
            return self._parse_data(plan, self.json_fields)
        except Exception as e:
            print(f"Error getting diet plan by ID: {str(e)}")
            return None

    async def update(self, plan_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные плана диеты

        Args:
            plan_id: ID плана диеты
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

            return await self.client.update_document(self.collection, plan_id, data_to_update)
        except Exception as e:
            print(f"Error updating diet plan: {str(e)}")
            return False

    async def delete(self, plan_id: str) -> bool:
        """
        Удаляет план диеты

        Args:
            plan_id: ID плана диеты

        Returns:
            bool: Результат удаления
        """
        try:
            return await self.client.delete_document(self.collection, plan_id)
        except Exception as e:
            print(f"Error deleting diet plan: {str(e)}")
            return False

    async def get_current_diet(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает текущий активный план диеты пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Текущий план диеты или None
        """
        try:
            query = """
                SELECT * FROM diet_plans
                WHERE user_id = $1 AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """

            plan = await self.client.fetchrow(query, user_id)

            if not plan:
                # Если нет активного плана, проверяем наличие ожидающего подтверждения
                query = """
                    SELECT * FROM diet_plans
                    WHERE user_id = $1 AND status = 'pending'
                    ORDER BY created_at DESC
                    LIMIT 1
                """

                plan = await self.client.fetchrow(query, user_id)

            return self._parse_data(plan, self.json_fields)
        except Exception as e:
            print(f"Error getting current diet: {str(e)}")
            return None

    async def get_user_plans(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Получает все планы пользователя

        Args:
            user_id: ID пользователя

        Returns:
            List[Dict[str, Any]]: Список планов пользователя
        """
        try:
            query = """
                SELECT * FROM diet_plans
                WHERE user_id = $1
                ORDER BY created_at DESC
            """

            plans = await self.client.fetch(query, user_id)
            return [self._parse_data(plan, self.json_fields) for plan in plans]
        except Exception as e:
            print(f"Error getting user plans: {str(e)}")
            return []

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
        try:
            # Получаем текущий план
            plan = await self.get_by_id(plan_id)
            if not plan:
                return False

            # Получаем ежедневные планы и обновляем конкретный день
            daily_plans = plan.get("daily_plans", {})
            daily_plans[day_key] = day_data

            # Обновляем план с обновленными данными
            return await self.update(plan_id, {
                "daily_plans": daily_plans,
                "updated_at": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error updating daily plan: {str(e)}")
            return False