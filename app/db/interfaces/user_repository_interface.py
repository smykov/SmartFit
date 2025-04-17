from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IUserRepository(ABC):
    """Интерфейс для работы с репозиторием пользователей"""

    @abstractmethod
    async def create(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Создает нового пользователя
        
        Args:
            user_data: Данные пользователя
            
        Returns:
            Optional[str]: ID созданного пользователя или None в случае ошибки
        """
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по ID
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[Dict[str, Any]]: Данные пользователя или None, если пользователь не найден
        """
        pass

    @abstractmethod
    async def get_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Получает пользователя по номеру телефона
        
        Args:
            phone_number: Номер телефона пользователя
            
        Returns:
            Optional[Dict[str, Any]]: Данные пользователя или None, если пользователь не найден
        """
        pass

    @abstractmethod
    async def update(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные пользователя
        
        Args:
            user_id: ID пользователя
            update_data: Данные для обновления
            
        Returns:
            bool: Результат обновления
        """
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """
        Удаляет пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: Результат удаления
        """
        pass

    @abstractmethod
    async def find_with_incomplete_onboarding(self) -> List[Dict[str, Any]]:
        """
        Находит пользователей с незавершенным онбордингом
        
        Returns:
            List[Dict[str, Any]]: Список пользователей с незавершенным онбордингом
        """
        pass

    @abstractmethod
    async def find_with_completed_onboarding(self) -> List[Dict[str, Any]]:
        """
        Находит пользователей с завершенным онбордингом

        Returns:
            List[Dict[str, Any]]: Список пользователей с завершенным онбордингом
        """
        pass
