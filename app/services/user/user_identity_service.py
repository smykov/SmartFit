# app/services/user/user_identity_service.py
import logging
from typing import Dict, Any, Optional, List, Tuple

from app.db.interfaces.user_repository_interface import IUserRepository

logger = logging.getLogger(__name__)


class UserIdentityService:
    """
    Сервис для управления идентичностью пользователей в разных мессенджерах
    """

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
        self.logger = logging.getLogger(self.__class__.__name__)

    async def link_messenger_account(self, user_id: str, messenger_type: str,
                                     messenger_id: str) -> bool:
        """
        Связывает аккаунт мессенджера с пользователем

        Args:
            user_id: ID пользователя
            messenger_type: Тип мессенджера
            messenger_id: ID в мессенджере

        Returns:
            bool: Результат операции
        """
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return False

            # Получаем текущие аккаунты или инициализируем пустой словарь
            messenger_accounts = user.get("messenger_accounts", {})

            # Добавляем новый аккаунт
            messenger_accounts[messenger_type] = messenger_id

            # Обновляем пользователя
            result = await self.user_repository.update(user_id, {
                "messenger_accounts": messenger_accounts
            })

            return result
        except Exception as e:
            self.logger.error(f"Error linking messenger account: {str(e)}")
            return False

    async def get_user_by_messenger_id(self, messenger_type: str,
                                       messenger_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по ID в мессенджере

        Args:
            messenger_type: Тип мессенджера
            messenger_id: ID в мессенджере

        Returns:
            Optional[Dict[str, Any]]: Данные пользователя или None
        """
        try:
            # Находим пользователя по аккаунту мессенджера
            # Это потребует нового метода в репозитории пользователей
            return await self.user_repository.find_by_messenger_account(
                messenger_type, messenger_id
            )
        except Exception as e:
            self.logger.error(f"Error getting user by messenger ID: {str(e)}")
            return None

    async def get_primary_messenger_id(self, user_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Получает основной ID мессенджера пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Tuple[Optional[str], Optional[str]]: (тип мессенджера, ID в мессенджере)
        """
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return None, None

            # Получаем предпочитаемый мессенджер
            preferred_messenger = user.get("preferred_messenger", "whatsapp")
            messenger_accounts = user.get("messenger_accounts", {})

            # Если у пользователя есть аккаунт в предпочитаемом мессенджере
            if preferred_messenger in messenger_accounts:
                return preferred_messenger, messenger_accounts[preferred_messenger]

            # Иначе берем первый доступный аккаунт
            if messenger_accounts:
                messenger_type = next(iter(messenger_accounts.keys()))
                return messenger_type, messenger_accounts[messenger_type]

            return None, None
        except Exception as e:
            self.logger.error(f"Error getting primary messenger ID: {str(e)}")
            return None, None