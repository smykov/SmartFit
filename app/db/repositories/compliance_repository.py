# app/db/repositories/compliance_repository.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date

import pytz

from app.db.interfaces.compliance_repository_interface import IComplianceRepository
from config import settings

logger = logging.getLogger(__name__)


class FirebaseComplianceRepository(IComplianceRepository):
    """
    Репозиторий для работы с записями соблюдения плана питания через Firebase
    """

    def __init__(self, firebase_client):
        """
        Инициализация репозитория записей соблюдения плана питания

        Args:
            firebase_client: Клиент Firebase для работы с базой данных
        """
        self.firebase_client = firebase_client

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
            compliance_id = self.firebase_client.add_document("meal_compliance", compliance_data)

            if not compliance_id:
                logger.error(f"Failed to save meal compliance for user {user_id}")
                return None

            # Обновляем общую статистику соблюдения
            await self.update_daily_compliance(user_id, date_str)

            return compliance_id

        except Exception as e:
            logger.error(f"Error adding meal compliance: {str(e)}")
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
            # Преобразуем в строку
            date_str = date_value.isoformat() if isinstance(date_value, date) else date_value

            # Получаем записи о соблюдении
            compliance_entries = self.firebase_client.query_documents(
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
                    "message": "Нет данных о соблюдении плана на этот день"
                }
                return empty_compliance

            return daily_compliance[0]

        except Exception as e:
            logger.error(f"Error getting daily compliance: {str(e)}")
            return None

    async def update_daily_compliance(self, user_id: str, date_value: date) -> bool:
        """
        Обновляет общую статистику соблюдения плана питания за день

        Args:
            user_id: ID пользователя
            date_value: Дата

        Returns:
            bool: Результат обновления
        """
        try:
            # Преобразуем в строку
            date_str = date_value.isoformat() if isinstance(date_value, date) else date_value

            # Получаем все записи о соблюдении за день
            compliances = self.firebase_client.query_documents(
                "meal_compliance",
                "user_id",
                "==",
                user_id
            )

            # Фильтруем по дате
            daily_compliances = [c for c in compliances if c.get("date") == date_str]

            if not daily_compliances:
                return False

            # Формируем словарь по типам приемов пищи
            meals_status = {}
            for compliance in daily_compliances:
                meal_type = compliance.get("meal_type")
                status = compliance.get("status")
                meals_status[meal_type] = status

            # Рассчитываем общий процент соблюдения
            score_map = {
                "followed": 1.0,
                "partially": 0.5,
                "substituted": 0.3,
                "skipped": 0.0,
                "not_recorded": 0.0
            }

            total_score = sum(score_map.get(status, 0) for status in meals_status.values())
            max_possible = len(meals_status) if meals_status else 1
            overall_score = (total_score / max_possible) * 100

            # Сохраняем общую статистику
            compliance_data = {
                "user_id": user_id,
                "date": date_str,
                "meals": meals_status,
                "overall_score": overall_score,
                "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            }

            # Проверяем, существует ли уже запись
            existing = self.firebase_client.query_documents(
                "daily_compliance",
                "user_id",
                "==",
                user_id
            )

            # Фильтруем по дате
            existing = [e for e in existing if e.get("date") == date_str]

            if existing:
                # Обновляем существующую запись
                return self.firebase_client.update_document(
                    "daily_compliance",
                    existing[0]["id"],
                    compliance_data
                )
            else:
                # Создаем новую запись
                compliance_id = self.firebase_client.add_document("daily_compliance", compliance_data)
                return bool(compliance_id)

        except Exception as e:
            logger.error(f"Error updating daily compliance: {str(e)}")
            return False

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
            compliance_entries = self.firebase_client.query_documents(
                "daily_compliance",
                "user_id",
                "==",
                user_id
            )

            # Фильтруем по дате
            filtered_entries = []
            for entry in compliance_entries:
                entry_date = entry.get("date", "")
                if entry_date >= start_str and entry_date <= end_str:
                    filtered_entries.append(entry)

            return filtered_entries

        except Exception as e:
            logger.error(f"Error getting compliance by period: {str(e)}")
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
            return self.firebase_client.delete_document(
                "meal_compliance",
                compliance_id
            )
        except Exception as e:
            logger.error(f"Error deleting compliance: {str(e)}")
            return False
