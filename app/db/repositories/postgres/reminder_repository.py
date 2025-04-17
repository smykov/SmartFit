# app/db/repositories/postgres/reminder_repository.py
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.db.interfaces.reminder_repository_interface import IReminderRepository
from app.db.postgres import PostgresClient
from app.db.repositories.postgres.base_repository import PostgresBaseRepository


# app/db/repositories/postgres_reminder_repository.py (продолжение)
class PostgresReminderRepository(PostgresBaseRepository, IReminderRepository):
    """
    Реализация репозитория напоминаний с использованием PostgreSQL
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Инициализация репозитория

        Args:
            postgres_client: Клиент PostgreSQL
        """
        super().__init__(postgres_client, "reminders")
        self.json_fields = []

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
            reminder_data = {
                "phone_number": phone_number,
                "reminder_type": reminder_type,
                "timestamp": datetime.now().isoformat()
            }

            prepared_data = self._prepare_data(reminder_data)
            reminder_id = await self.client.add_document(self.collection, prepared_data)

            return reminder_id is not None
        except Exception as e:
            print(f"Error saving reminder: {str(e)}")
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
            query = """
                SELECT * FROM reminders
                WHERE phone_number = $1 AND reminder_type = $2
                ORDER BY timestamp DESC
                LIMIT 1
            """

            reminder = await self.client.fetchrow(query, phone_number, reminder_type)
            return self._parse_data(reminder, self.json_fields)
        except Exception as e:
            print(f"Error getting last reminder: {str(e)}")
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
            # Вычисляем время для указанного периода
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

            query = """
                SELECT * FROM reminders
                WHERE phone_number = $1 
                AND reminder_type = $2 
                AND timestamp > $3
                ORDER BY timestamp DESC
            """

            reminders = await self.client.fetch(query, phone_number, reminder_type, cutoff_time)
            return [self._parse_data(reminder, self.json_fields) for reminder in reminders]
        except Exception as e:
            print(f"Error getting reminders for period: {str(e)}")
            return []