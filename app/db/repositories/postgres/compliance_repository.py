# app/db/repositories/postgres/compliance_repository.py
import json
from datetime import date, datetime
from typing import Dict, Any, List, Optional

from app.db.interfaces.compliance_repository_interface import IComplianceRepository
from app.db.postgres import PostgresClient
from app.db.repositories.postgres.base_repository import PostgresBaseRepository


class PostgresComplianceRepository(PostgresBaseRepository, IComplianceRepository):
    """
    Реализация репозитория записей соблюдения плана питания с использованием PostgreSQL
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Инициализация репозитория

        Args:
            postgres_client: Клиент PostgreSQL
        """
        super().__init__(postgres_client, "compliance")
        self.json_fields = ["meals"]
        self.daily_collection = "daily_compliance"

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
            date_str = date_value.isoformat()

            # Создаем запись о соблюдении приема пищи
            compliance_data = {
                "user_id": user_id,
                "date": date_str,
                "meal_type": meal_type,
                "status": status,
                "notes": notes,
                "alternative_meal": alternative_meal,
                "created_at": datetime.now().isoformat()
            }

            prepared_data = self._prepare_data(compliance_data)
            compliance_id = await self.client.add_document(self.collection, prepared_data)

            # Обновляем общую статистику соблюдения на день
            await self.update_daily_compliance(user_id, date_value)

            return compliance_id
        except Exception as e:
            print(f"Error adding meal compliance: {str(e)}")
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
            date_str = date_value.isoformat()

            query = """
                SELECT * FROM daily_compliance
                WHERE user_id = $1 AND date = $2
            """

            compliance = await self.client.fetchrow(query, user_id, date_str)

            # Если записи не существует, создаем ее
            if not compliance:
                await self.update_daily_compliance(user_id, date_value)
                compliance = await self.client.fetchrow(query, user_id, date_str)

            return self._parse_data(compliance, self.json_fields)
        except Exception as e:
            print(f"Error getting daily compliance: {str(e)}")
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
            date_str = date_value.isoformat()

            # Получаем все записи о соблюдении за день
            query = """
                SELECT * FROM compliance
                WHERE user_id = $1 AND date = $2
            """

            compliance_records = await self.client.fetch(query, user_id, date_str)

            # Создаем словарь с информацией о соблюдении по приемам пищи
            meals = {}

            for record in compliance_records:
                meal_type = record.get("meal_type")
                status = record.get("status")

                if meal_type and status:
                    meals[meal_type] = status

            # Расчет общего процента соблюдения
            overall_score = self._calculate_compliance_score(meals)

            # Проверяем существование записи
            daily_query = """
                SELECT id FROM daily_compliance
                WHERE user_id = $1 AND date = $2
            """

            existing = await self.client.fetchrow(daily_query, user_id, date_str)

            if existing:
                # Обновляем существующую запись
                await self.client.update_document(
                    self.daily_collection,
                    existing["id"],
                    {
                        "meals": json.dumps(meals),
                        "overall_score": overall_score,
                        "updated_at": datetime.now().isoformat()
                    }
                )
            else:
                # Создаем новую запись
                daily_data = {
                    "user_id": user_id,
                    "date": date_str,
                    "meals": meals,
                    "overall_score": overall_score,
                    "updated_at": datetime.now().isoformat()
                }

                prepared_data = self._prepare_data(daily_data)
                await self.client.add_document(self.daily_collection, prepared_data)

            return True
        except Exception as e:
            print(f"Error updating daily compliance: {str(e)}")
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
            start_date_str = start_date.isoformat()
            end_date_str = end_date.isoformat()

            query = """
                SELECT * FROM daily_compliance
                WHERE user_id = $1 AND date >= $2 AND date <= $3
                ORDER BY date
            """

            records = await self.client.fetch(query, user_id, start_date_str, end_date_str)
            return [self._parse_data(record, self.json_fields) for record in records]
        except Exception as e:
            print(f"Error getting compliance by period: {str(e)}")
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
            # Получаем информацию о записи для последующего обновления суточной статистики
            record = await self.client.get_document(self.collection, compliance_id)

            if not record:
                return False

            user_id = record.get("user_id")
            date_str = record.get("date")

            # Удаляем запись
            result = await self.client.delete_document(self.collection, compliance_id)

            if result and user_id and date_str:
                # Обновляем суточную статистику
                try:
                    date_obj = date.fromisoformat(date_str)
                    await self.update_daily_compliance(user_id, date_obj)
                except ValueError:
                    pass

            return result
        except Exception as e:
            print(f"Error deleting compliance: {str(e)}")
            return False

    def _calculate_compliance_score(self, meals: Dict[str, str]) -> float:
        """
        Расчет общего процента соблюдения плана питания

        Args:
            meals: Словарь {тип приема пищи: статус}

        Returns:
            float: Процент соблюдения (0-100)
        """
        if not meals:
            return 0.0

        # Веса для разных статусов соблюдения
        status_weights = {
            "followed": 1.0,
            "partially": 0.5,
            "substituted": 0.3,
            "skipped": 0.0
        }

        total_weight = 0.0
        max_weight = 0.0

        for meal_type, status in meals.items():
            weight = status_weights.get(status, 0.0)
            total_weight += weight
            max_weight += 1.0

        if max_weight == 0:
            return 0.0

        return (total_weight / max_weight) * 100.0