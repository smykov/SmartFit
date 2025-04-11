# app/db/interfaces/water_entry_repository_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import date, datetime


class IWaterEntryRepository(ABC):
    """
    Интерфейс для работы с репозиторием записей потребления воды
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_daily_total(self, user_id: str, date_value: date = None) -> float:
        """
        Получает общее потребление воды за день

        Args:
            user_id: ID пользователя
            date_value: Дата (по умолчанию - текущая дата)

        Returns:
            float: Общее потребление воды в мл за день
        """
        pass

    @abstractmethod
    async def update_entry(self, entry_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет запись потребления воды

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
        Удаляет запись потребления воды

        Args:
            entry_id: ID записи

        Returns:
            bool: Результат удаления
        """
        pass