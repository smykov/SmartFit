# app/db/repositories/postgres_user_repository.py
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.db.interfaces.user_repository_interface import IUserRepository
from app.db.postgres import PostgresClient
from app.db.repositories.postgres.base_repository import PostgresBaseRepository


class PostgresUserRepository(PostgresBaseRepository, IUserRepository):
    """
    Реализация репозитория пользователей с использованием PostgreSQL
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Инициализация репозитория

        Args:
            postgres_client: Клиент PostgreSQL
        """
        super().__init__(postgres_client, "users")
        self.json_fields = ["allergies", "disliked_products"]

    async def create(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает нового пользователя

        Args:
            user_data: Данные пользователя

        Returns:
            Optional[str]: ID созданного пользователя или None в случае ошибки
        """
        try:
            prepared_data = self._prepare_data(user_data)
            return await self.client.add_document(self.collection, prepared_data)
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return None

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по ID

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Данные пользователя или None, если пользователь не найден
        """
        try:
            user = await self.client.get_document(self.collection, user_id)
            return self._parse_data(user, self.json_fields)
        except Exception as e:
            print(f"Error getting user by ID: {str(e)}")
            return None

    async def get_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по номеру телефона

        Args:
            phone_number: Номер телефона пользователя

        Returns:
            Optional[Dict[str, Any]]: Данные пользователя или None, если пользователь не найден
        """
        try:
            users = await self.client.query_documents(self.collection, "phone_number", "==", phone_number)
            if users and len(users) > 0:
                return self._parse_data(users[0], self.json_fields)
            return None
        except Exception as e:
            print(f"Error getting user by phone: {str(e)}")
            return None

    async def update(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные пользователя

        Args:
            user_id: ID пользователя
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

            return await self.client.update_document(self.collection, user_id, data_to_update)
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            return False

    async def delete(self, user_id: str) -> bool:
        """
        Удаляет пользователя

        Args:
            user_id: ID пользователя

        Returns:
            bool: Результат удаления
        """
        try:
            return await self.client.delete_document(self.collection, user_id)
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            return False

    async def find_with_incomplete_onboarding(self) -> List[Dict[str, Any]]:
        """
        Находит пользователей с незавершенным онбордингом

        Returns:
            List[Dict[str, Any]]: Список пользователей с незавершенным онбордингом
        """
        try:
            query = """
                SELECT * FROM users
                WHERE is_onboarding_completed = false
            """

            users = await self.client.fetch(query)
            return [self._parse_data(user, self.json_fields) for user in users]
        except Exception as e:
            print(f"Error finding users with incomplete onboarding: {str(e)}")
            return []