# app/db/repositories/compliance_repository.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date

import pytz

import data
from app.db.interfaces.compliance_repository_interface import IComplianceRepository
from app.models.tracking import MealComplianceStatus
from config import settings

class FirebaseComplianceRepository(IComplianceRepository):
    """
    Репозиторий для работы с записями соблюдения плана питания через Firebase
    """

    def __init__(self, firebase_client, diet_plan_repository=None):
        """
        Инициализация репозитория записей соблюдения плана питания

        Args:
            firebase_client: Клиент Firebase для работы с базой данных
            diet_plan_repository: Репозиторий плана диеты (опционально)
        """
        self.firebase_client = firebase_client
        self.diet_plan_repository = diet_plan_repository
        self.logger = logging.getLogger(self.__class__.__name__)

    async def add_meal_compliance(self, user_id: str, date_value: date, meal_type: str,
                                  status: str, notes: str = None,
                                  alternative_meal: str = None) -> Optional[str]:
        """
        Добавляет запись о соблюдении приема пищи

        Args:
            user_id: ID пользователя
            date_value: Дата
            meal_type: Тип приема пищи (breakfast, lunch, dinner, snack)
            status: Статус соблюдения (followed, partially, substituted, skipped)
            notes: Дополнительные заметки
            alternative_meal: Альтернативное блюдо (если status=substituted)

        Returns:
            Optional[str]: ID созданной записи или None в случае ошибки
        """
        try:
            # Формируем дату в формате строки
            date_str = date_value.isoformat() if isinstance(date_value, date) else date_value

            # Создаем запись о соблюдении режима
            compliance_data = {
                "user_id": user_id,
                "date": date_str,
                "meal_type": meal_type,
                "status": status,
                "notes": notes,
                "alternative_meal": alternative_meal,
                "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            }

            # Сохраняем в базу данных
            compliance_id = await self.firebase_client.add_document("meal_compliance", compliance_data)

            if not compliance_id:
                self.logger.error(f"Failed to save meal compliance for user {user_id}")
                return None

            return compliance_id

        except Exception as e:
            self.logger.error(f"Error adding meal compliance: {str(e)}")
            return None

    async def get_daily_compliance(self, user_id: str, date_value: date) -> Optional[Dict[str, Any]]:
        """
        Получает статистику соблюдения плана питания за день

        Args:
            user_id: ID пользователя
            date_value: Дата

        Returns:
            Optional[Dict[str, Any]]: Статистика соблюдения или None
        """
        try:

            # Формируем дату в формате строки
            date_str = date_value.isoformat() if isinstance(date_value, date) else date_value

            # Получаем записи о соблюдении
            compliance_entries = await self.firebase_client.query_documents(
                "daily_compliance",
                "user_id",
                "==",
                user_id
            )

            # Фильтруем по дате
            daily_compliance = [c for c in compliance_entries if c.get("date") == date_str]

            if not daily_compliance:
                # Если записи нет, создаем пустую запись
                empty_compliance = {
                    "user_id": user_id,
                    "date": date_str,
                    "meals": {},
                    "overall_score": 0,
                    "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                    "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                }
                return empty_compliance

            return daily_compliance[0]

        except Exception as e:
            self.logger.error(f"Error getting daily compliance: {str(e)}")
            return None

    async def update_daily_compliance(self, user_id: str, date_value: date) -> bool:
        """
        Обновляет данные о соблюдении плана питания на день

        Args:
            user_id: ID пользователя
            date_value: Дата

        Returns:
            bool: Результат операции
        """
        try:
            # Формируем дату в формате строки
            date_str = date_value.isoformat() if isinstance(date_value, date) else date_value

            # Получаем текущие данные о соблюдении или создаем новую запись
            compliance_data = await self.get_daily_compliance(user_id, date_value)

            # Получаем список приемов пищи
            meal_data = compliance_data.get("meals", {})

            # Рассчитываем процент соблюдения
            total_value = 0

            # Получаем все запланированные приемы пищи на этот день
            planned_meals = await self.get_planned_meals_for_day(user_id, date_value)

            # Если нет запланированных приемов пищи, используем отмеченные
            total_meals = len(planned_meals) if planned_meals else len(meal_data)

            compliance_data["overall_score"] = 0.0

            if total_meals > 0:
                # Учитываем все запланированные приемы пищи
                for planned_meal in planned_meals:
                    meal_status = meal_data.get(planned_meal, MealComplianceStatus.SKIPPED.value)

                    # Определяем вес статуса
                    status_weight = 0
                    if meal_status == MealComplianceStatus.FOLLOWED.value:
                        status_weight = 1.0
                    elif meal_status == MealComplianceStatus.PARTIALLY.value:
                        status_weight = 0.5
                    elif meal_status == MealComplianceStatus.SUBSTITUTED.value:
                        status_weight = 0.25

                    total_value += status_weight

                # Рассчитываем процент
                percentage = (total_value / total_meals) * 100
                compliance_data["overall_score"] = round(percentage, 1)

            # Обновляем временную метку
            compliance_data["updated_at"] = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()

            # Проверяем, существует ли уже запись в БД (есть ли id)
            compliance_id = compliance_data.get("id")
            collection_name = "daily_compliance"

            if compliance_id:
                # Если запись существует, обновляем её
                result = await self.firebase_client.update_document(collection_name, compliance_id, compliance_data)
            else:
                # Если записи нет, создаем новую
                compliance_id = await self.firebase_client.add_document(collection_name, compliance_data)
                result = bool(compliance_id)

            # Логируем для отладки
            self.logger.info(f"Updating compliance for {user_id} on {date_str}: {compliance_data}")

            return result

        except Exception as e:
            self.logger.error(f"Error updating daily compliance: {str(e)}", exc_info=True)
            return False

    # Метод для получения всех запланированных приемов пищи на день
    async def get_planned_meals_for_day(self, user_id: str, date_value: date) -> List[str]:
        """
        Получает список всех запланированных приемов пищи на день

        Args:
            user_id: ID пользователя
            date_value: Дата

        Returns:
            List[str]: Список типов приемов пищи
        """
        try:
            # Получаем план диеты
            diet_plan = await self.diet_plan_repository.get_current_diet(user_id)
            if not diet_plan:
                return []

            # Определяем день недели
            day_of_week = date_value.strftime("%A").lower()

            # Получаем план на день
            daily_plan = diet_plan.get("daily_plans", {}).get(day_of_week, {})

            # Получаем все типы приемов пищи из плана
            meals = daily_plan.get("meals", [])
            meal_types = [meal.get("type") for meal in meals if meal.get("type")]

            return meal_types

        except Exception as e:
            self.logger.error(f"Error getting planned meals for day: {str(e)}")
            return []
    async def get_compliance_by_period(self, user_id: str, start_date: date,
                                       end_date: date) -> List[Dict[str, Any]]:
        """
        Получает статистику соблюдения плана питания за период

        Args:
            user_id: ID пользователя
            start_date: Начальная дата периода
            end_date: Конечная дата периода

        Returns:
            List[Dict[str, Any]]: Список статистик соблюдения по дням
        """
        try:
            # Преобразуем даты в строки
            start_str = start_date.isoformat() if isinstance(start_date, date) else start_date
            end_str = end_date.isoformat() if isinstance(end_date, date) else end_date

            # Получаем все записи о соблюдении
            compliance_entries = await self.firebase_client.query_documents(
                "daily_compliance",
                "user_id",
                "==",
                user_id
            )

            # Фильтруем по дате
            filtered_entries = []
            for entry in compliance_entries:
                entry_date = entry.get("date", "")
                if start_str <= entry_date <= end_str:
                    filtered_entries.append(entry)

            return filtered_entries

        except Exception as e:
            self.logger.error(f"Error getting compliance by period: {str(e)}")
            return []

    async def delete_compliance(self, compliance_id: str) -> bool:
        """
        Удаляет запись о соблюдении плана питания

        Args:
            compliance_id: ID записи

        Returns:
            bool: Результат удаления
        """
        try:
            return await self.firebase_client.delete_document(
                "meal_compliance",
                compliance_id
            )
        except Exception as e:
            self.logger.error(f"Error deleting compliance: {str(e)}")
            return False
