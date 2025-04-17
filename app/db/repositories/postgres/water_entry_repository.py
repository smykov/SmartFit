# app/db/repositories/postgres/water_entry_repository.py
from datetime import date, datetime
from typing import Dict, Any, List, Optional

from app.db.interfaces.water_entry_repository_interface import IWaterEntryRepository
from app.db.postgres import PostgresClient
from app.db.repositories.postgres.base_repository import PostgresBaseRepository


class PostgresWaterEntryRepository(PostgresBaseRepository, IWaterEntryRepository):
    """
    Реализация репозитория записей потребления воды с использованием PostgreSQL
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Инициализация репозитория

        Args:
            postgres_client: Клиент PostgreSQL
        """
        super().__init__(postgres_client, "water_entries")
        self.json_fields = []

    async def add_entry(self, user_id: str, amount: float, date_value: date = None,
                        time_value: datetime = None) -> Optional[str]:
        """
        Добавляет новую запись потребления воды

        Args:
            user_id: ID пользователя
            amount: Количество воды в мл
            date_value: Дата записи (по умолчанию - текущая дата)
            time_value: Время записи (по умолчанию - текущее время)

        Returns:
            Optional[str]: ID созданной записи или None в случае ошибки
        """
        try:
            now = datetime.now()
            entry_data = {
                "user_id": user_id,
                "amount": amount,
                "date": date_value.isoformat() if date_value else now.date().isoformat(),
                "time": time_value.isoformat() if time_value else now.isoformat(),
                "created_at": now.isoformat()
            }

            prepared_data = self._prepare_data(entry_data)
            return await self.client.add_document(self.collection, prepared_data)
        except Exception as e:
            print(f"Error adding water entry: {str(e)}")
            return None

    async def get_entries_by_user(self, user_id: str, start_date: date = None,
                                  end_date: date = None) -> List[Dict[str, Any]]:
        """
        Получает записи потребления воды пользователя за период

        Args:
            user_id: ID пользователя
            start_date: Начальная дата периода (если None, то без ограничения)
            end_date: Конечная дата периода (если None, то без ограничения)

        Returns:
            List[Dict[str, Any]]: Список записей потребления воды
        """
        try:
            conditions = ["user_id = $1"]
            params = [user_id]

            if start_date:
                param_index = len(params) + 1
                conditions.append(f"date >= ${param_index}")
                params.append(start_date.isoformat())

            if end_date:
                param_index = len(params) + 1
                conditions.append(f"date <= ${param_index}")
                params.append(end_date.isoformat())

            query = f"""
                SELECT * FROM water_entries
                WHERE {" AND ".join(conditions)}
                ORDER BY date, time
            """

            entries = await self.client.fetch(query, *params)
            return [self._parse_data(entry, self.json_fields) for entry in entries]
        except Exception as e:
            print(f"Error getting water entries by user: {str(e)}")
            return []

    async def get_daily_total(self, user_id: str, date_value: date = None) -> float:
        """
        Получает общее потребление воды за день

        Args:
            user_id: ID пользователя
            date_value: Дата (по умолчанию - текущая дата)

        Returns:
            float: Общее потребление воды в мл за день
        """
        try:
            date_str = date_value.isoformat() if date_value else date.today().isoformat()

            query = """
                SELECT COALESCE(SUM(amount), 0) as total FROM water_entries
                WHERE user_id = $1 AND date = $2
            """

            result = await self.client.fetchrow(query, user_id, date_str)

            if result and "total" in result:
                return float(result["total"])

            return 0.0
        except Exception as e:
            print(f"Error getting daily total water: {str(e)}")
            return 0.0

    async def update_entry(self, entry_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет запись потребления воды

        Args:
            entry_id: ID записи
            update_data: Данные для обновления

        Returns:
            bool: Результат обновления
        """
        try:
            update_data["updated_at"] = datetime.now().isoformat()
            return await self.client.update_document(self.collection, entry_id, update_data)
        except Exception as e:
            print(f"Error updating water entry: {str(e)}")
            return False

    async def delete_entry(self, entry_id: str) -> bool:
        """
        Удаляет запись потребления воды

        Args:
            entry_id: ID записи

        Returns:
            bool: Результат удаления
        """
        try:
            return await self.client.delete_document(self.collection, entry_id)
        except Exception as e:
            print(f"Error deleting water entry: {str(e)}")
            return False