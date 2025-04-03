# app/db/interfaces/reminder_repository.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IReminderRepository(ABC):
    """Интерфейс для репозитория напоминаний"""

    @abstractmethod
    async def save_reminder(self, phone_number: str, reminder_type: str) -> bool:
        """
        Сохраняет информацию об отправленном напоминании

        Args:
            phone_number: Номер телефона пользователя
            reminder_type: Тип напоминания

        Returns:
            bool: Результат операции
        """
        pass

    @abstractmethod
    async def get_last_reminder(self, phone_number: str, reminder_type: str) -> Optional[Dict[str, Any]]:
        """
        Получает последнее напоминание определенного типа для пользователя

        Args:
            phone_number: Номер телефона пользователя
            reminder_type: Тип напоминания

        Returns:
            Optional[Dict[str, Any]]: Информация о последнем напоминании или None
        """
        pass

    @abstractmethod
    async def get_reminders_for_period(
            self, phone_number: str, reminder_type: str, hours: int
    ) -> List[Dict[str, Any]]:
        """
        Получает напоминания определенного типа за указанный период

        Args:
            phone_number: Номер телефона пользователя
            reminder_type: Тип напоминания
            hours: Количество часов для периода

        Returns:
            List[Dict[str, Any]]: Список напоминаний
        """
        pass