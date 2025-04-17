# app/db/repositories/postgres/weight_entry_repository.py
from datetime import date, datetime
from typing import Dict, Any, List, Optional

from app.db.interfaces.weight_entry_repository_interface import IWeightEntryRepository
from app.db.postgres import PostgresClient
from app.db.repositories.postgres.base_repository import PostgresBaseRepository


class PostgresWeightEntryRepository(PostgresBaseRepository, IWeightEntryRepository):
    """
    Реализация репозитория записей веса с использованием PostgreSQL
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Инициализация репозитория

        Args:
            postgres_client: Клиент PostgreSQL
        """
        super().__init__(postgres_client, "weight_entries")
        self.json_fields = []

    async def add_entry(self, user_id: str, weight: float, date_value: date = None, notes: str = None) -> Optional[str]:
        """
        Добавляет новую запись веса

        Args:
            user_id: ID пользователя
            weight: Вес в кг
            date_value: Дата записи (по умолчанию - текущая дата)
            notes: Дополнительные заметки

        Returns:
            Optional[str]: ID созданной записи или None в случае ошибки
        """
        try:
            entry_data = {
                "user_id": user_id,
                "weight": weight,
                "date": date_value.isoformat() if date_value else date.today().isoformat(),
                "notes": notes if notes else None,
                "created_at": datetime.now().isoformat()
            }

            prepared_data = self._prepare_data(entry_data)
            return await self.client.add_document(self.collection, prepared_data)
        except Exception as e:
            print(f"Error adding weight entry: {str(e)}")
            return None

    async def get_entries_by_user(self, user_id: str, start_date: date = None,
                                  end_date: date = None) -> List[Dict[str, Any]]:
        """
        Получает записи веса пользователя за период

        Args:
            user_id: ID пользователя
            start_date: Начальная дата периода (если None, то без ограничения)
            end_date: Конечная дата периода (если None, то без ограничения)

        Returns:
            List[Dict[str, Any]]: Список записей веса
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
                SELECT * FROM weight_entries
                WHERE {" AND ".join(conditions)}
                ORDER BY date
            """

            entries = await self.client.fetch(query, *params)
            return [self._parse_data(entry, self.json_fields) for entry in entries]
        except Exception as e:
            print(f"Error getting weight entries by user: {str(e)}")
            return []

    async def get_latest_entry(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает последнюю запись веса пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Последняя запись веса или None
        """
        try:
            query = """
                SELECT * FROM weight_entries
                WHERE user_id = $1
                ORDER BY date DESC
                LIMIT 1
            """

            entry = await self.client.fetchrow(query, user_id)
            return self._parse_data(entry, self.json_fields)
        except Exception as e:
            print(f"Error getting latest weight entry: {str(e)}")
            return None

    async def update_entry(self, entry_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет запись веса

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
            print(f"Error updating weight entry: {str(e)}")
            return False

    async def delete_entry(self, entry_id: str) -> bool:
        """
        Удаляет запись веса

        Args:
            entry_id: ID записи

        Returns:
            bool: Результат удаления
        """
        try:
            return await self.client.delete_document(self.collection, entry_id)
        except Exception as e:
            print(f"Error deleting weight entry: {str(e)}")
            return False