import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import pytz

from app.db.interfaces.message_repository_interface import IMessageRepository
from app.models.messaging import MessageStatus
from config import settings


class FirebaseMessageRepository(IMessageRepository):
    """
    Репозиторий для работы с сообщениями в Firebase
    """

    def __init__(self, firebase_client):
        """
        Инициализация репозитория с сообщениями

        Args:
            firebase_client: Клиент Firebase для работы с базой данных
        """
        self.firebase_client = firebase_client
        self.logger = logging.getLogger(self.__class__.__name__)

    async def save_message(self, message_data: Dict[str, Any]) -> str:
        """
        Сохраняет сообщение в репозитории

        Args:
            message_data: Словарь с данными сообщения

        Returns:
            str: Идентификатор сохраненного сообщения
        """
        try:
            # Добавляем временную метку, если её нет
            if "timestamp" not in message_data:
                message_data["timestamp"] = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()

            # Сохраняем в Firebase
            message_id = await self.firebase_client.add_document("messages", message_data)

            return message_id or ""

        except Exception as e:
            self.logger.error(f"Error saving message: {str(e)}")
            return ""

    async def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает сообщение по его идентификатору

        Args:
            message_id: Уникальный идентификатор сообщения

        Returns:
            Optional[Dict[str, Any]]: Данные сообщения или None
        """
        try:
            message = await self.firebase_client.get_document("messages", message_id)
            return message

        except Exception as e:
            self.logger.error(f"Error getting message by id: {str(e)}")
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
                "status": MessageStatus.SENT,
                "timestamp": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            }

            # Добавляем контекст, если он предоставлен
            if context:
                self.logger.info(f"save_sent_message - context: {context}")
                message_data.update(context)

            # Сохраняем в коллекции sent_messages
            result = await self.firebase_client.add_document("sent_messages", message_data)
            return bool(result)

        except Exception as e:
            self.logger.error(f"Error saving sent message: {str(e)}")
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
            now = datetime.now(pytz.timezone(settings.TIMEZONE))

            message_data = {
                "phone_number": phone_number,
                "message_text": message_text,
                "status": MessageStatus.PENDING,
                "error_type": error_type,
                "attempts": 1,
                "timestamp": now.isoformat(),
                "last_attempt": now.isoformat()
            }

            # Добавляем контекст, если он предоставлен
            if context:
                message_data.update(context)

            # Проверяем наличие дубликата
            existing_messages = await self.firebase_client.query_documents(
                "pending_messages",
                "phone_number", "==", phone_number
            )

            # Фильтруем, чтобы найти сообщения с таким же текстом и статусом pending
            duplicate_messages = [
                msg for msg in existing_messages
                if msg.get("status") == MessageStatus.PENDING and msg.get("message_text") == message_text
            ]

            if duplicate_messages:
                # Если нашли дубликат, просто обновляем его, увеличивая счетчик попыток
                duplicate = duplicate_messages[0]
                await self.firebase_client.update_document(
                    "pending_messages",
                    duplicate.get("id"),
                    {
                        "attempts": duplicate.get("attempts", 1) + 1,
                        "last_attempt": now.isoformat(),
                        "error_type": error_type
                    }
                )
                self.logger.info(f"Updated existing pending message (id: {duplicate.get('id')})")
            else:
                # Если дубликата нет, создаем новую запись
                await self.firebase_client.add_document("pending_messages", message_data)
                self.logger.info(f"Created new pending message for {phone_number}")

            return True

        except Exception as e:
            self.logger.error(f"Error saving pending message: {str(e)}")
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
            pending_messages = await self.firebase_client.query_documents(
                "pending_messages",
                "status", "==", MessageStatus.PENDING
            )

            # Если указан максимальный возраст, фильтруем сообщения
            if max_age_hours is not None:
                now = datetime.now(pytz.timezone(settings.TIMEZONE))
                max_age_delta = now - timedelta(hours=max_age_hours)

                # Фильтруем сообщения по возрасту
                pending_messages = [
                    msg for msg in pending_messages
                    if datetime.fromisoformat(msg.get("timestamp", "2100-01-01")) > max_age_delta
                ]

            return pending_messages

        except Exception as e:
            self.logger.error(f"Error finding pending messages: {str(e)}")
            return []

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
            # Получаем сообщение из базы данных
            message = await self.firebase_client.get_document("pending_messages", message_id)

            if not message:
                self.logger.warning(f"Pending message {message_id} not found")
                return False

            # Создаем запись в sent_messages
            sent_data = {
                "phone_number": message.get("phone_number"),
                "message_id": provider_message_id,
                "message_text": message.get("message_text"),
                "status": MessageStatus.SENT,
                "timestamp": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                "original_timestamp": message.get("timestamp"),
                "attempts": message.get("attempts", 1)
            }

            # Копируем контекст, если он есть
            if "onboarding_step" in message:
                sent_data["onboarding_step"] = message["onboarding_step"]

            # Записываем в sent_messages
            await self.firebase_client.add_document("sent_messages", sent_data)

            # Удаляем из pending_messages
            await self.firebase_client.delete_document("pending_messages", message_id)

            return True

        except Exception as e:
            self.logger.error(f"Error marking pending message as sent: {str(e)}")
            return False

    async def mark_pending_message_as_expired(self, message_id: str) -> bool:
        """
        Помечает неотправленное сообщение как устаревшее

        Args:
            message_id: ID сообщения

        Returns:
            bool: Успешность операции
        """
        try:
            return await self.firebase_client.update_document(
                "pending_messages",
                message_id,
                {
                    "status": MessageStatus.EXPIRED,
                    "expired_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
                }
            )

        except Exception as e:
            self.logger.error(f"Error marking pending message as expired: {str(e)}")
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
            # Получаем сообщение из базы данных
            message = await self.firebase_client.get_document("pending_messages", message_id)

            if not message:
                self.logger.warning(f"Pending message {message_id} not found")
                return False

            # Увеличиваем счетчик попыток
            return await self.firebase_client.update_document(
                "pending_messages",
                message_id,
                {
                    "attempts": message.get("attempts", 1) + 1,
                    "last_attempt": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
                }
            )

        except Exception as e:
            self.logger.error(f"Error updating pending message attempts: {str(e)}")
            return False

    async def is_processed(self, message_id: str) -> bool:
        """
        Проверяет, было ли сообщение обработано

        Args:
            message_id: Идентификатор сообщения

        Returns:
            bool: Статус обработки сообщения
        """
        try:
            processed_messages = await self.firebase_client.query_documents(
                "processed_messages",
                "message_id", "==", message_id
            )

            return len(processed_messages) > 0

        except Exception as e:
            self.logger.error(f"Error checking if message is processed: {str(e)}")
            return False

    async def mark_as_processing(self, message_id: str, phone_number: str, message_text: str, timestamp: str) -> bool:
        """
        Отмечает сообщение как находящееся в обработке

        Args:
            message_id: ID сообщения
            phone_number: ID отправителя
            message_text: Текст сообщения
            timestamp: Временная метка

        Returns:
            bool: Результат операции
        """
        try:
            message_data = {
                "message_id": message_id,
                "phone_number": phone_number,
                "message_text": message_text,
                "status": "processing",
                "timestamp": timestamp
            }

            # Запись в базу данных
            await self.firebase_client.set_document("processed_messages", message_id, message_data)
            return True
        except Exception as e:
            self.logger.error(f"Error marking message as processing: {str(e)}")
            return False

    async def mark_as_processed(self, message_id: str, phone_number: str, message_text: str, timestamp: str) -> bool:
        """
        Помечает сообщение как обработанное

        Args:
            message_id: Идентификатор сообщения
            phone_number: Номер телефона отправителя
            message_text: Текст сообщения
            timestamp: Временная метка обработки
        """
        try:
            result = await self.firebase_client.add_document("processed_messages", {
                "message_id": message_id,
                "phone_number": phone_number,
                "message_text": message_text,
                "status": "processed",
                "processed_at": timestamp
            })
            if not result:
                return False

            return True
        except Exception as e:
            self.logger.error(f"Error marking message as processed: {str(e)}")
            return False

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
            # Сначала получаем все сообщения
            all_messages = await self.firebase_client.get_all_documents("messages")

            # Постепенно фильтруем по критериям
            filtered_messages = all_messages

            # Фильтр по номеру телефона
            if phone_number:
                filtered_messages = [msg for msg in filtered_messages
                                     if msg.get("phone_number") == phone_number]

            # Фильтр по начальной дате
            if start_date:
                start_date_str = start_date.isoformat()
                filtered_messages = [msg for msg in filtered_messages
                                     if msg.get("timestamp", "") >= start_date_str]

            # Фильтр по конечной дате
            if end_date:
                end_date_str = end_date.isoformat()
                filtered_messages = [msg for msg in filtered_messages
                                     if msg.get("timestamp", "") <= end_date_str]

            # Фильтр по типу сообщения
            if message_type:
                filtered_messages = [msg for msg in filtered_messages
                                     if msg.get("message_type") == message_type]

            return filtered_messages

        except Exception as e:
            self.logger.error(f"Error finding messages by criteria: {str(e)}")
            return []

    async def count_messages_by_user(self, phone_number: str) -> int:
        """
        Подсчитывает количество сообщений от конкретного пользователя

        Args:
            phone_number: Номер телефона пользователя

        Returns:
            int: Количество сообщений
        """
        try:
            # Получаем сообщения для указанного номера телефона
            messages = await self.firebase_client.query_documents(
                "messages",
                "phone_number", "==", phone_number
            )

            return len(messages)

        except Exception as e:
            self.logger.error(f"Error counting messages for user {phone_number}: {str(e)}")
            return 0


    async def get_message_status(self, message_id: str) -> Optional[str]:
        """
        Получает статус сообщения

        Args:
            message_id: ID сообщения

        Returns:
            Optional[str]: Статус сообщения или None
        """
        pass


    async def mark_as_failed(self, message_id: str, error: str) -> bool:
        """
        Отмечает сообщение как обработанное с ошибкой

        Args:
            message_id: ID сообщения
            error: Текст ошибки

        Returns:
            bool: Результат операции
        """
        pass