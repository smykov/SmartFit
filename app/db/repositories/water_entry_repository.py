# app/db/repositories/water_entry_repository.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date

import pytz

from app.db.interfaces.water_entry_repository_interface import IWaterEntryRepository
from config import settings

logger = logging.getLogger(__name__)


class FirebaseWaterEntryRepository(IWaterEntryRepository):
    """
    Репозиторий для работы с записями потребления воды через Firebase
    """

    def __init__(self, firebase_client):
        """
        Инициализация репозитория записей потребления воды

        Args:
            firebase_client: Клиент Firebase для работы с базой данных
        """
        self.firebase_client = firebase_client

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
            # Если дата не указана, используем текущую
            if date_value is None:
                date_value = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Если время не указано, используем текущее
            if time_value is None:
                time_value = datetime.now(pytz.timezone(settings.TIMEZONE))

            # Преобразуем дату в строку
            date_str = date_value.isoformat()

            # Получаем пользователя для обновления истории потребления воды
            user = await self.firebase_client.get_document("users", user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            # Обновляем историю потребления воды пользователя
            water_history = user.get("water_intake_history", {})

            # Если на сегодня уже есть запись, добавляем к ней
            if date_str in water_history:
                water_history[date_str] += amount
            else:
                water_history[date_str] = amount

            await self.firebase_client.update_document("users", user_id, {"water_intake_history": water_history})

            # Создаем запись в коллекции water_entries для аналитики
            entry_data = {
                "user_id": user_id,
                "amount": amount,
                "date": date_str,
                "time": time_value.isoformat(),
                "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            }

            entry_id = await self.firebase_client.add_document("water_entries", entry_data)
            return entry_id

        except Exception as e:
            logger.error(f"Error adding water entry: {str(e)}")
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
            # Получаем все записи потребления воды пользователя
            entries = await self.firebase_client.query_documents(
                "water_entries",
                "user_id",
                "==",
                user_id
            )

            # Фильтруем по дате, если указаны ограничения
            if start_date or end_date:
                filtered_entries = []
                for entry in entries:
                    try:
                        entry_date = datetime.strptime(entry.get("date", ""), "%Y-%m-%d").date()

                        # Проверяем соответствие дате
                        if (not start_date or entry_date >= start_date) and \
                                (not end_date or entry_date <= end_date):
                            filtered_entries.append(entry)
                    except (ValueError, TypeError):
                        # Пропускаем записи с неверным форматом даты
                        continue

                return filtered_entries

            return entries

        except Exception as e:
            logger.error(f"Error getting water entries: {str(e)}")
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
            # Если дата не указана, используем текущую
            if date_value is None:
                date_value = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            date_str = date_value.isoformat()

            # Получаем пользователя
            user = await self.firebase_client.get_document("users", user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return 0.0

            # Получаем историю потребления воды
            water_history = user.get("water_intake_history", {})

            # Возвращаем потребление за указанную дату или 0, если записи нет
            return float(water_history.get(date_str, 0.0))

        except Exception as e:
            logger.error(f"Error getting daily water total: {str(e)}")
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
            return await self.firebase_client.update_document(
                "water_entries",
                entry_id,
                update_data
            )
        except Exception as e:
            logger.error(f"Error updating water entry: {str(e)}")
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
            return await self.firebase_client.delete_document(
                "water_entries",
                entry_id
            )
        except Exception as e:
            logger.error(f"Error deleting water entry: {str(e)}")
            return False