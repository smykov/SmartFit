import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pytz

from app.db.interfaces.user_repository_interface import IUserRepository
from config import settings

logger = logging.getLogger(__name__)


class FirebaseUserRepository(IUserRepository):
    """Репозиторий для работы с пользователями через Firebase"""

    def __init__(self, firebase_client):
        """
        Инициализация репозитория пользователей

        Args:
            firebase_client: Клиент Firebase для работы с базой данных
        """
        self.firebase_client = firebase_client

    async def create(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает нового пользователя

        Args:
            user_data: Данные пользователя

        Returns:
            Optional[str]: ID созданного пользователя или None в случае ошибки
        """
        try:
            now = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            if 'created_at' not in user_data:
                user_data['created_at'] = now
            user_data['updated_at'] = now

            user_id = await self.firebase_client.add_document("users", user_data)

            return user_id
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
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
            user = await self.firebase_client.get_document("users", user_id)
            return user
        except Exception as e:
            logger.error(f"Error retrieving user by ID: {str(e)}")
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
            users = await self.firebase_client.query_documents("users", "phone_number", "==", phone_number)
            if not users:
                return None
            return users[0]
        except Exception as e:
            logger.error(f"Error retrieving user by phone: {str(e)}")
            return None

    async def get_by_chat_id(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по номеру телефона

        Args:
            chat_id: Номер телефона пользователя

        Returns:
            Optional[Dict[str, Any]]: Данные пользователя или None, если пользователь не найден
        """
        try:
            users = await self.firebase_client.query_documents("users", "chat_id", "==", chat_id)
            if not users:
                return None
            return users[0]
        except Exception as e:
            logger.error(f"Error retrieving user by phone: {str(e)}")
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
            return await self.firebase_client.update_document("users", user_id, update_data)
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
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
            # В реальном приложении часто делают "soft delete" вместо физического удаления
            return await self.firebase_client.update_document("users", user_id, {"is_active": False})
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False

    async def find_with_incomplete_onboarding(self) -> List[Dict[str, Any]]:
        """
        Находит пользователей с незавершенным онбордингом

        Returns:
            List[Dict[str, Any]]: Список пользователей с незавершенным онбордингом
        """
        try:
            return await self.firebase_client.query_documents("users", "is_onboarding_completed", "==", False)
        except Exception as e:
            logger.error(f"Error finding users with incomplete onboarding: {str(e)}")
            return []

    async def find_with_completed_onboarding(self) -> List[Dict[str, Any]]:
        """
        Находит пользователей с завершенным онбордингом

        Returns:
            List[Dict[str, Any]]: Список пользователей с завершенным онбордингом
        """
        try:
            return await self.firebase_client.query_documents("users", "is_onboarding_completed", "==", True)
        except Exception as e:
            logger.error(f"Error finding users with completed onboarding: {str(e)}")
            return []


    async def find_by_messenger_account(self, messenger_type: str,
                                        messenger_id: str) -> Optional[Dict[str, Any]]:
        """
        Находит пользователя по аккаунту мессенджера

        Args:
            messenger_type: Тип мессенджера
            messenger_id: ID в мессенджере

        Returns:
            Optional[Dict[str, Any]]: Данные пользователя или None
        """
        try:
            # Создаем путь к вложенному полю
            field_path = f"messenger_accounts.{messenger_type}"

            # Выполняем запрос к Firebase
            users = await self.firebase_client.query_documents("users", field_path, "==", messenger_id)

            if not users:
                return None

            return users[0]
        except Exception as e:
            logger.error(f"Error finding user by messenger account: {str(e)}")
            return None