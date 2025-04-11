# app/db/interfaces/weight_entry_repository_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import date


class IWeightEntryRepository(ABC):
    """
    Интерфейс для работы с репозиторием записей веса
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_latest_entry(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает последнюю запись веса пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Последняя запись веса или None
        """
        pass

    @abstractmethod
    async def update_entry(self, entry_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет запись веса

        Args:
            entry_id: ID записи
            update_data: Данные для обновления

        Returns:
            bool: Результат обновления
        """
        pass

    @abstractmethod
    async def delete_entry(self, entry_id: str) -> bool:
        """
        Удаляет запись веса

        Args:
            entry_id: ID записи

        Returns:
            bool: Результат удаления
        """
        pass