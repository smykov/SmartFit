# app/db/repositories/weight_entry_repository.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date

import pytz

from app.db.interfaces.weight_entry_repository_interface import IWeightEntryRepository
from config import settings

logger = logging.getLogger(__name__)


class FirebaseWeightEntryRepository(IWeightEntryRepository):
    """
    Репозиторий для работы с записями веса через Firebase
    """

    def __init__(self, firebase_client):
        """
        Инициализация репозитория записей веса

        Args:
            firebase_client: Клиент Firebase для работы с базой данных
        """
        self.firebase_client = firebase_client

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
            # Если дата не указана, используем текущую
            if date_value is None:
                date_value = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Преобразуем дату в строку
            date_str = date_value.isoformat()

            # Получаем пользователя для обновления текущего веса
            user = self.firebase_client.get_document("users", user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            # Обновляем текущий вес пользователя
            self.firebase_client.update_document("users", user_id, {"current_weight": weight})

            # Обновляем историю веса пользователя
            weight_history = user.get("weight_history", {})
            weight_history[date_str] = weight
            self.firebase_client.update_document("users", user_id, {"weight_history": weight_history})

            # Создаем запись в коллекции weight_entries для аналитики
            entry_data = {
                "user_id": user_id,
                "weight": weight,
                "date": date_str,
                "notes": notes,
                "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            }

            entry_id = self.firebase_client.add_document("weight_entries", entry_data)
            return entry_id

        except Exception as e:
            logger.error(f"Error adding weight entry: {str(e)}")
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
            # Получаем все записи веса пользователя
            entries = self.firebase_client.query_documents(
                "weight_entries",
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
            logger.error(f"Error getting weight entries: {str(e)}")
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
            # Получаем все записи веса пользователя
            entries = self.firebase_client.query_documents(
                "weight_entries",
                "user_id",
                "==",
                user_id
            )

            if not entries:
                return None

            # Сортируем по дате (от новых к старым)
            sorted_entries = sorted(
                entries,
                key=lambda entry: entry.get("date", ""),
                reverse=True
            )

            return sorted_entries[0] if sorted_entries else None

        except Exception as e:
            logger.error(f"Error getting latest weight entry: {str(e)}")
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
            return self.firebase_client.update_document(
                "weight_entries",
                entry_id,
                update_data
            )
        except Exception as e:
            logger.error(f"Error updating weight entry: {str(e)}")
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
            return self.firebase_client.delete_document(
                "weight_entries",
                entry_id
            )
        except Exception as e:
            logger.error(f"Error deleting weight entry: {str(e)}")
            return False