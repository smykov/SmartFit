# app/db/repositories/reminder_repository.py

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import pytz

from app.db.interfaces.reminder_repository_interface import IReminderRepository
from app.utils.date_helper import DateHelper
from config import settings


class FirebaseReminderRepository(IReminderRepository):
    """Репозиторий для работы с напоминаниями в Firebase"""

    def __init__(self, firebase_client):
        """
        Инициализация репозитория напоминаний

        Args:
            firebase_client: Клиент Firebase для работы с базой данных
        """
        self.firebase_client = firebase_client
        self.collection_name = "reminders"
        self.logger = logging.getLogger(self.__class__.__name__)

    async def save_reminder(self, phone_number: str, reminder_type: str) -> bool:
        """
        Сохраняет информацию об отправленном напоминании

        Args:
            phone_number: Номер телефона пользователя
            reminder_type: Тип напоминания

        Returns:
            bool: Результат операции
        """
        try:
            # Создаем данные о напоминании
            reminder_data = {
                "phone_number": phone_number,
                "reminder_type": reminder_type,
                "timestamp": DateHelper.get_current_datetime().isoformat(),
                "status": "sent"
            }

            # Сохраняем напоминание в коллекцию
            reminder_id = await self.firebase_client.add_document(self.collection_name, reminder_data)

            if not reminder_id:
                self.logger.error(f"Failed to save reminder for phone {phone_number}")
                return False

            self.logger.info(f"Reminder saved successfully: {reminder_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving reminder: {str(e)}")
            return False

    async def get_last_reminder(self, phone_number: str, reminder_type: str) -> Optional[Dict[str, Any]]:
        """
        Получает последнее напоминание определенного типа для пользователя

        Args:
            phone_number: Номер телефона пользователя
            reminder_type: Тип напоминания

        Returns:
            Optional[Dict[str, Any]]: Информация о последнем напоминании или None
        """
        try:
            # Используем новый метод для составных запросов
            conditions = [
                ("phone_number", "==", phone_number),
                ("reminder_type", "==", reminder_type)
            ]

            reminders = await self.firebase_client.query_documents_compound(
                self.collection_name,
                conditions
            )

            if not reminders:
                return None

            # Сортируем по времени (от последнего к старым)
            sorted_reminders = sorted(
                reminders,
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )

            # Возвращаем самое последнее напоминание
            return sorted_reminders[0] if sorted_reminders else None

        except Exception as e:
            self.logger.error(f"Error getting last reminder: {str(e)}")
            return None

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
        try:
            # Вычисляем время начала периода
            start_time = DateHelper.get_current_datetime() - timedelta(hours=hours)
            start_time_str = start_time.isoformat()

            conditions = [
                ("phone_number", "==", phone_number),
                ("reminder_type", "==", reminder_type)
            ]

            reminders = await self.firebase_client.query_documents_compound(
                self.collection_name,
                conditions
            )

            if not reminders:
                return []

            # Фильтруем напоминания по времени
            recent_reminders = [
                reminder for reminder in reminders
                if reminder.get("timestamp", "") >= start_time_str
            ]

            # Сортируем по времени (от последнего к ранним)
            return sorted(
                recent_reminders,
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )

        except Exception as e:
            self.logger.error(f"Error getting reminders for period: {str(e)}")
            return []

    async def delete_old_reminders(self, days: int = 30) -> int:
        """
        Удаляет старые напоминания

        Args:
            days: Количество дней, старше которых напоминания будут удалены

        Returns:
            int: Количество удаленных напоминаний
        """
        try:
            # Вычисляем время, старше которого напоминания будут удалены
            cut_off_date = DateHelper.get_current_datetime() - timedelta(days=days)
            cut_off_date_str = cut_off_date.isoformat()

            # Получаем все старые напоминания
            old_reminders = await self.firebase_client.query_documents(
                self.collection_name,
                field="timestamp",
                operator="<",
                value=cut_off_date_str
            )

            if not old_reminders:
                return 0

            # Удаляем каждое старое напоминание
            deleted_count = 0
            for reminder in old_reminders:
                if "id" in reminder:
                    success = await self.firebase_client.delete_document(self.collection_name, reminder["id"])
                    if success:
                        deleted_count += 1

            self.logger.info(f"Deleted {deleted_count} old reminders")
            return deleted_count

        except Exception as e:
            self.logger.error(f"Error deleting old reminders: {str(e)}")
            return 0

    async def count_reminders_by_type(self, reminder_type: str, hours: int = 24) -> int:
        """
        Подсчитывает количество напоминаний определенного типа за последние часы

        Args:
            reminder_type: Тип напоминания
            hours: Количество часов для периода

        Returns:
            int: Количество напоминаний
        """
        try:
            # Вычисляем время начала периода
            start_time = DateHelper.get_current_datetime() - timedelta(hours=hours)
            start_time_str = start_time.isoformat()

            # Получаем все напоминания данного типа
            reminders = await self.firebase_client.query_documents(
                self.collection_name,
                field="reminder_type",
                operator="==",
                value=reminder_type
            )

            if not reminders:
                return 0

            # Подсчитываем напоминания в заданный период
            count = sum(1 for reminder in reminders if reminder.get("timestamp", "") >= start_time_str)

            return count

        except Exception as e:
            self.logger.error(f"Error counting reminders by type: {str(e)}")
            return 0
