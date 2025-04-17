# app/db/repositories/diet_plan_repository.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pytz

from app.db.interfaces.diet_plan_repository_interface import IDietPlanRepository
from config import settings

logger = logging.getLogger(__name__)


class FirebaseDietPlanRepository(IDietPlanRepository):
    """
    Репозиторий для работы с планами диет через Firebase
    """

    def __init__(self, firebase_client):
        """
        Инициализация репозитория диет

        Args:
            firebase_client: Клиент Firebase для работы с базой данных
        """
        self.firebase_client = firebase_client

    async def create(self, diet_plan_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает новый план диеты

        Args:
            diet_plan_data: Данные плана диеты

        Returns:
            Optional[str]: ID созданного плана или None в случае ошибки
        """
        try:
            # Добавляем timestamp
            now = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            if 'created_at' not in diet_plan_data:
                diet_plan_data['created_at'] = now
            diet_plan_data['updated_at'] = now

            plan_id = self.firebase_client.add_document("diet_plans", diet_plan_data)

            if not plan_id:
                logger.error("Failed to create diet plan")
                return None

            return plan_id
        except Exception as e:
            logger.error(f"Error creating diet plan: {str(e)}")
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
            plan = self.firebase_client.get_document("diet_plans", plan_id)
            return plan
        except Exception as e:
            logger.error(f"Error getting diet plan by ID: {str(e)}")
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
            # Добавляем timestamp обновления
            update_data['updated_at'] = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()

            result = self.firebase_client.update_document("diet_plans", plan_id, update_data)
            return result
        except Exception as e:
            logger.error(f"Error updating diet plan: {str(e)}")
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
            result = self.firebase_client.delete_document("diet_plans", plan_id)
            return result
        except Exception as e:
            logger.error(f"Error deleting diet plan: {str(e)}")
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
            # Получаем все планы пользователя
            diet_plans = self.firebase_client.query_documents("diet_plans", "user_id", "==", user_id)

            if not diet_plans:
                return None

            # Сначала ищем полную версию с активным статусом
            active_plans = [plan for plan in diet_plans if
                            plan.get("status") == "active" and plan.get("version") == "full"]

            if active_plans:
                # Сортируем по дате создания (от новых к старым)
                return sorted(active_plans, key=lambda p: p.get("created_at", ""), reverse=True)[0]

            # Если нет активных полных планов, ищем согласованный краткий план
            approved_plans = [plan for plan in diet_plans if
                              plan.get("status") == "approved" and plan.get("version") == "short"]

            if approved_plans:
                # Сортируем по дате создания (от новых к старым)
                return sorted(approved_plans, key=lambda p: p.get("created_at", ""), reverse=True)[0]

            # Если нет ни активных полных, ни согласованных кратких, возвращаем последний план в ожидании согласования
            pending_plans = [plan for plan in diet_plans if plan.get("status") == "pending"]

            if pending_plans:
                # Сортируем по дате создания (от новых к старым)
                return sorted(pending_plans, key=lambda p: p.get("created_at", ""), reverse=True)[0]

            return None

        except Exception as e:
            logger.error(f"Error getting current diet: {str(e)}")
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
            pending_plans = self.firebase_client.query_documents("diet_plans", "user_id", "==", user_id)
            return pending_plans
        except Exception as e:
            logger.error(f"Error getting user plans: {str(e)}")
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
                logger.error(f"Plan with ID {plan_id} not found")
                return False

            # Обновляем план на день
            if "daily_plans" not in plan:
                plan["daily_plans"] = {}

            plan["daily_plans"][day_key] = day_data

            # Обновляем timestamp
            plan["updated_at"] = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()

            # Сохраняем обновленный план
            result = self.firebase_client.update_document(
                "diet_plans",
                plan_id,
                {
                    "daily_plans": plan["daily_plans"],
                    "updated_at": plan["updated_at"]
                }
            )

            return result

        except Exception as e:
            logger.error(f"Error updating daily plan: {str(e)}")
            return False

    async def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Находит планы диет по статусу

        Args:
            status: Статус планов для поиска

        Returns:
            List[Dict[str, Any]]: Список планов с указанным статусом
        """
        try:
            return self.firebase_client.query_documents("diet_plans", "status", "==", status)
        except Exception as e:
            logger.error(f"Error finding diet plans by status: {str(e)}")
            return []
