# app/db/repositories/postgres/message_repository.py
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.db.interfaces.message_repository_interface import IMessageRepository
from app.db.postgres import PostgresClient
from app.db.repositories.postgres.base_repository import PostgresBaseRepository


class PostgresMessageRepository(PostgresBaseRepository, IMessageRepository):
    """
    Реализация репозитория сообщений с использованием PostgreSQL
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Инициализация репозитория

        Args:
            postgres_client: Клиент PostgreSQL
        """
        super().__init__(postgres_client, "messages")
        self.json_fields = ["context"]

    async def save_message(self, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Сохраняет сообщение в репозитории

        Args:
            message_data: Словарь с данными сообщения

        Returns:
            str: Идентификатор сохраненного сообщения
        """
        try:
            prepared_data = self._prepare_data(message_data)
            message_id = await self.client.add_document(self.collection, prepared_data)
            return message_id
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return None

    async def save_sent_message(self, phone_number: str, message_id: str, message_text: str,
                                context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Сохраняет информацию об отправленном сообщении

        Args:
            phone_number: Номер телефона получателя
            message_id: ID сообщения от провайдера (например, Twilio)
            message_text: Текст сообщения
            context: Дополнительный контекст сообщения

        Returns:
            bool: Успешность операции
        """
        try:
            message_data = {
                "phone_number": phone_number,
                "message_id": message_id,
                "message_text": message_text,
                "status": "sent",
                "timestamp": datetime.now().isoformat(),
                "context": context or {}
            }

            prepared_data = self._prepare_data(message_data)
            await self.client.add_document(self.collection, prepared_data)
            return True
        except Exception as e:
            print(f"Error saving sent message: {str(e)}")
            return False

    async def update_pending_message_attempts(self, message_id: str) -> bool:
        """
        Обновляет счетчик попыток для неотправленного сообщения

        Args:
            message_id: ID сообщения

        Returns:
            bool: Успешность операции
        """
        try:
            # Получаем текущее сообщение для обновления счетчика
            message = await self.client.get_document(self.collection, message_id)
            if not message:
                return False

            attempts = message.get("attempts", 0) + 1
            last_attempt = datetime.now().isoformat()

            # Обновляем счетчик попыток и время последней попытки
            await self.client.update_document(self.collection, message_id, {
                "attempts": attempts,
                "last_attempt": last_attempt,
                "updated_at": datetime.now().isoformat()
            })

            return True
        except Exception as e:
            print(f"Error updating pending message attempts: {str(e)}")
            return False

    async def mark_pending_message_as_sent(self, message_id: str, provider_message_id: str) -> bool:
        """
        Помечает неотправленное сообщение как отправленное

        Args:
            message_id: ID сообщения в репозитории
            provider_message_id: ID сообщения от провайдера (например, Twilio)

        Returns:
            bool: Успешность операции
        """
        try:
            # Обновляем статус сообщения
            await self.client.update_document(self.collection, message_id, {
                "status": "sent",
                "provider_message_id": provider_message_id,
                "updated_at": datetime.now().isoformat()
            })

            return True
        except Exception as e:
            print(f"Error marking pending message as sent: {str(e)}")
            return False

    async def save_pending_message(self, phone_number: str, message_text: str, error_type: str = "unknown",
                                   context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Сохраняет информацию о неотправленном сообщении для повторной попытки

        Args:
            phone_number: Номер телефона получателя
            message_text: Текст сообщения
            error_type: Тип ошибки при отправке
            context: Дополнительный контекст сообщения

        Returns:
            bool: Успешность операции
        """
        try:
            message_data = {
                "phone_number": phone_number,
                "message_text": message_text,
                "status": "pending",
                "error_type": error_type,
                "attempts": 0,
                "timestamp": datetime.now().isoformat(),
                "context": context or {}
            }

            prepared_data = self._prepare_data(message_data)
            await self.client.add_document(self.collection, prepared_data)
            return True
        except Exception as e:
            print(f"Error saving pending message: {str(e)}")
            return False

    async def find_pending_messages(self, max_age_hours: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Находит все неотправленные сообщения

        Args:
            max_age_hours: Максимальный возраст сообщений в часах

        Returns:
            List[Dict[str, Any]]: Список неотправленных сообщений
        """
        try:
            query = """
                SELECT * FROM messages
                WHERE status = 'pending'
            """

            # Если указан максимальный возраст, добавляем условие
            if max_age_hours:
                cutoff_time = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
                query += f" AND timestamp > '{cutoff_time}'"

            query += " ORDER BY timestamp ASC"

            pending_messages = await self.client.fetch(query)
            return [self._parse_data(message, self.json_fields) for message in pending_messages]
        except Exception as e:
            print(f"Error finding pending messages: {str(e)}")
            return []

    async def mark_pending_message_as_expired(self, message_id: str) -> bool:
        """
        Помечает неотправленное сообщение как устаревшее

        Args:
            message_id: ID сообщения

        Returns:
            bool: Успешность операции
        """
        try:
            # Обновляем статус сообщения
            await self.client.update_document(self.collection, message_id, {
                "status": "expired",
                "updated_at": datetime.now().isoformat()
            })

            return True
        except Exception as e:
            print(f"Error marking pending message as expired: {str(e)}")
            return False

    async def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает сообщение по его идентификатору

        Args:
            message_id: Уникальный идентификатор сообщения

        Returns:
            Optional[Dict[str, Any]]: Данные сообщения или None
        """
        try:
            message = await self.client.get_document(self.collection, message_id)
            return self._parse_data(message, self.json_fields)
        except Exception as e:
            print(f"Error getting message by ID: {str(e)}")
            return None

    async def find_messages_by_criteria(
            self,
            phone_number: Optional[str] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            message_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Находит сообщения по заданным критериям

        Args:
            phone_number: Номер телефона отправителя
            start_date: Начальная дата для поиска
            end_date: Конечная дата для поиска
            message_type: Тип сообщения

        Returns:
            List[Dict[str, Any]]: Список найденных сообщений
        """
        try:
            conditions = []
            params = []

            if phone_number:
                conditions.append("phone_number = $1")
                params.append(phone_number)

            if start_date:
                param_index = len(params) + 1
                conditions.append(f"timestamp >= ${param_index}")
                params.append(start_date.isoformat())

            if end_date:
                param_index = len(params) + 1
                conditions.append(f"timestamp <= ${param_index}")
                params.append(end_date.isoformat())

            if message_type:
                param_index = len(params) + 1
                conditions.append(f"message_type = ${param_index}")
                params.append(message_type)

            query = "SELECT * FROM messages"

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY timestamp DESC"

            messages = await self.client.fetch(query, *params)
            return [self._parse_data(message, self.json_fields) for message in messages]
        except Exception as e:
            print(f"Error finding messages by criteria: {str(e)}")
            return []

    async def is_processed(self, message_id: str) -> bool:
        """
        Проверяет, было ли сообщение обработано

        Args:
            message_id: Идентификатор сообщения

        Returns:
            bool: Статус обработки сообщения
        """
        try:
            query = """
                SELECT is_processed FROM messages
                WHERE id = $1
            """

            result = await self.client.fetchrow(query, message_id)

            if result and "is_processed" in result:
                return result["is_processed"]

            return False
        except Exception as e:
            print(f"Error checking if message is processed: {str(e)}")
            return False

    async def mark_as_processed(
            self,
            message_id: str,
            phone_number: str,
            message_text: str,
            timestamp: str
    ) -> None:
        """
        Помечает сообщение как обработанное

        Args:
            message_id: Идентификатор сообщения
            phone_number: Номер телефона отправителя
            message_text: Текст сообщения
            timestamp: Временная метка обработки
        """
        try:
            # Проверяем, существует ли сообщение
            existing_message = await self.client.get_document(self.collection, message_id)

            if existing_message:
                # Обновляем существующее сообщение
                await self.client.update_document(self.collection, message_id, {
                    "is_processed": True,
                    "updated_at": datetime.now().isoformat()
                })
            else:
                # Создаем новую запись
                message_data = {
                    "id": message_id,
                    "phone_number": phone_number,
                    "message_text": message_text,
                    "timestamp": timestamp,
                    "is_processed": True
                }

                prepared_data = self._prepare_data(message_data)
                await self.client.add_document(self.collection, prepared_data)
        except Exception as e:
            print(f"Error marking message as processed: {str(e)}")

    async def count_messages_by_user(self, phone_number: str) -> int:
        """
        Подсчитывает количество сообщений от конкретного пользователя

        Args:
            phone_number: Номер телефона пользователя

        Returns:
            int: Количество сообщений
        """
        try:
            query = """
                SELECT COUNT(*) as count FROM messages
                WHERE phone_number = $1
            """

            result = await self.client.fetchrow(query, phone_number)

            if result and "count" in result:
                return result["count"]

            return 0
        except Exception as e:
            print(f"Error counting messages by user: {str(e)}")
            return 0