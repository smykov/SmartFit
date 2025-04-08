# app/services/messaging/whatsapp_service.py
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import pytz

from app.db.interfaces.message_repository_interface import IMessageRepository
from app.services.messaging.interfaces.message_client_interface import IMessageClient
from app.services.localization.localization_interface import ILocalizationService
from app.utils.text_splitter import TextSplitter
from config import settings

logger = logging.getLogger(__name__)


def _log_error_with_context(message: str, exception: Optional[Exception] = None,
                            context: Optional[Dict[str, Any]] = None):
    """
    Расширенное логирование ошибок с контекстом

    Args:
        message: Сообщение об ошибке
        exception: Исключение
        context: Дополнительный контекст
    """
    error_message = f"{message}"

    if exception:
        error_message += f": {str(exception)}"

    if context:
        error_message += f" [Context: {context}]"

    logger.error(error_message)


class WhatsAppService:
    """
    Сервис для работы с WhatsApp API, ответственный за отправку и обработку сообщений
    """

    def __init__(self,
                 message_client: IMessageClient,
                 message_repository: IMessageRepository,
                 localization_service: ILocalizationService,
                 text_splitter: TextSplitter,
                 from_phone_number: str,
                 retry_interval_seconds: int = 300,
                 max_message_size: int = 1500,
                 max_message_age_hours: int = 72):
        """
        Инициализация сервиса WhatsApp

        Args:
            message_client: Клиент для отправки сообщений
            message_repository: Репозиторий для работы с сообщениями
            localization_service: Сервис локализации сообщений
            text_splitter: Утилита для разбиения текста на части
            from_phone_number: Номер телефона отправителя
            retry_interval_seconds: Интервал между повторными попытками отправки (в секундах)
            max_message_size: Максимальный размер сообщения
            max_message_age_hours: Максимальный возраст сообщений в часах
        """
        self.message_client = message_client
        self.message_repository = message_repository
        self.localization_service = localization_service
        self.text_splitter = text_splitter
        self.from_phone_number = from_phone_number
        self.retry_interval_seconds = retry_interval_seconds
        self.max_message_size = max_message_size
        self.max_message_age_hours = max_message_age_hours

    async def initialize(self):
        """Инициализация сервиса и запуск регулярных задач"""
        try:
            logger.info("Initializing WhatsApp service...")

            # Запускаем отправку отложенных сообщений
            await self._resend_all_pending_messages()

            # Запускаем периодическую задачу для отправки отложенных сообщений
            asyncio.create_task(self._schedule_resend_pending_messages())

            logger.info("WhatsApp service initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing WhatsApp service: {str(e)}")

    async def send_message(self, to_phone: str, message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет текстовое сообщение по WhatsApp

        Args:
            to_phone: Номер телефона получателя
            message: Текст сообщения
            context: Дополнительный контекст сообщения (шаг онбординга и т.д.)

        Returns:
            bool: Результат отправки
        """
        try:
            # Проверяем размер сообщения
            if len(message) > self.max_message_size:
                return await self.send_chunked_message(to_phone, message, context)

            # Отправляем сообщение через клиент
            message_id = await self.message_client.send_message(to_phone, message)

            if message_id:
                # Сохраняем информацию об отправленном сообщении
                await self.message_repository.save_sent_message(to_phone, message_id, message, context)
                logger.info(f"Message sent successfully: {message_id}")
                return True
            else:
                # Сохраняем сообщение для повторной отправки
                error_type = "whatsapp_api_error"
                await self.message_repository.save_pending_message(to_phone, message, error_type, context)
                logger.warning(f"Failed to send message to {to_phone}, saved for retry")
                return False

        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")

            # Сохраняем сообщение для повторной отправки
            await self.message_repository.save_pending_message(to_phone, message, "general_error", context)

            return False

    async def send_chunked_message(self, to_phone: str, message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Разбивает длинное сообщение на части и отправляет последовательно

        Args:
            to_phone: Номер телефона получателя
            message: Текст сообщения
            context: Дополнительный контекст сообщения

        Returns:
            bool: Результат отправки (True, если все части отправлены успешно)
        """
        try:
            # Разбиваем сообщение на части
            parts = self.text_splitter.split_text(message, self.max_message_size)

            # Отправляем части
            success = True
            total_parts = len(parts)

            for idx, part in enumerate(parts):
                part_marker = f"[{idx + 1}/{total_parts}] "
                formatted_part = f"{'(продолжение) ' if idx > 0 else ''}{part}"
                full_part = part_marker + formatted_part

                # Создаем контекст для части
                part_context = context.copy() if context else {}
                part_context["part_index"] = idx
                part_context["total_parts"] = total_parts

                # Отправляем часть
                part_success = await self.send_message(to_phone, full_part, part_context)
                success = success and part_success

                # Небольшая задержка между отправками
                await asyncio.sleep(0.5)

            return success

        except Exception as e:
            logger.error(f"Error sending chunked message: {str(e)}")

            # Сохраняем сообщение для повторной отправки, но только первую часть
            await self.message_repository.save_pending_message(
                to_phone,
                message[:self.max_message_size] + "...",
                "chunking_error",
                context
            )

            return False

    async def send_messages(self, to_phone: str, messages: List[str], context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет несколько текстовых сообщений последовательно

        Args:
            to_phone: Номер телефона получателя
            messages: Список текстовых сообщений
            context: Дополнительный контекст сообщений

        Returns:
            bool: Результат отправки (True, если все сообщения отправлены успешно)
        """
        try:
            success = True

            for idx, message in enumerate(messages):
                # Создаем контекст для сообщения
                message_context = context.copy() if context else {}
                message_context["message_index"] = idx
                message_context["total_messages"] = len(messages)

                # Отправляем сообщение
                message_success = await self.send_message(to_phone, message, message_context)
                success = success and message_success

                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.5)

            return success

        except Exception as e:
            logger.error(f"Error sending multiple messages: {str(e)}")
            return False

    async def send_template_message(self, to_phone: str, template_name: str, user_id: Optional[str] = None,
                                    params: Dict[str, Any] = None, ) -> bool:
        """
        Отправляет локализованное шаблонное сообщение через WhatsApp

        Args:
            to_phone: Номер телефона получателя
            template_name: Ключ шаблона сообщения
            user_id: ID пользователя для определения языка (если None, используется язык по умолчанию)
            params: Параметры для подстановки в шаблон

        Returns:
            bool: Результат отправки
        """
        try:
            # Определяем язык пользователя, если предоставлен ID
            lang = None
            if user_id:
                lang = await self.localization_service.get_user_language(user_id)

            # Отправляем шаблонное сообщение через клиент
            message_id = await self.message_client.send_template_message(
                to_phone,
                template_name,
                lang,
                params
            )

            if message_id:
                # Создаем контекст для шаблонного сообщения
                template_context = {
                    "template_name": template_name,
                    "template_params": params,
                    "language": lang,
                    "user_id": user_id
                }

                # Сохраняем информацию об отправленном сообщении
                await self.message_repository.save_sent_message(
                    to_phone,
                    message_id,
                    f"Template: {template_name}",
                    template_context
                )

                logger.info(f"Template message sent successfully: {message_id}")
                return True
            else:
                # Сохраняем сообщение для повторной отправки
                error_type = "template_send_error"
                template_context = {
                    "template_name": template_name,
                    "template_params": params,
                    "language": lang,
                    "user_id": user_id
                }

                await self.message_repository.save_pending_message(
                    to_phone,
                    f"Template: {template_name}",
                    error_type,
                    template_context
                )

                logger.warning(f"Failed to send template message to {to_phone}, saved for retry")
                return False

        except Exception as e:
            logger.error(f"Error sending template message: {str(e)}")
            return False

    async def _resend_all_pending_messages(self):
        """Отправляет все неотправленные сообщения"""
        try:
            # Получаем неотправленные сообщения
            pending_messages = await self.message_repository.find_pending_messages(self.max_message_age_hours)

            if not pending_messages:
                logger.info("No pending messages found to resend")
                return

            logger.info(f"Found {len(pending_messages)} pending messages to resend")

            # Группируем сообщения по номеру телефона для более эффективной отправки
            messages_by_phone = {}

            for message in pending_messages:
                phone = message.get("phone_number")
                if phone not in messages_by_phone:
                    messages_by_phone[phone] = []
                messages_by_phone[phone].append(message)

            # Обрабатываем сообщения для каждого номера телефона
            for phone_number, messages in messages_by_phone.items():
                # Сортируем по времени (от ранних к поздним)
                sorted_messages = sorted(messages, key=lambda x: x.get("timestamp", ""))

                # Ограничиваем количество отправляемых сообщений
                for message in sorted_messages[:5]:  # Не более 5 сообщений за раз
                    # Проверяем, не устарело ли сообщение
                    timestamp = datetime.fromisoformat(message.get("timestamp", ""))
                    now = datetime.now(pytz.timezone(settings.TIMEZONE))

                    if (now - timestamp).total_seconds() > self.max_message_age_hours * 3600:
                        # Помечаем как устаревшее
                        await self.message_repository.mark_pending_message_as_expired(message.get("id"))
                        logger.info(f"Marked expired message: {message.get('id')}")
                        continue

                    # Извлекаем данные сообщения
                    message_text = message.get("message_text", "")
                    message_id = message.get("id")

                    # Создаем контекст из существующих метаданных
                    context = {k: v for k, v in message.items() if k not in
                               ["id", "phone_number", "message_text", "status", "attempts",
                                "timestamp", "last_attempt", "error_type"]}

                    # Добавляем префикс для старых сообщений
                    if (now - timestamp).total_seconds() > 3600:  # Старше 1 часа
                        message_text = f"📳 Отложенное сообщение:\n\n{message_text}"

                    # Проверяем, является ли это шаблонным сообщением
                    if "template_name" in context:
                        # Отправляем как шаблонное сообщение
                        success = await self.send_template_message(
                            phone_number,
                            context["template_name"],
                            context.get("user_id"),
                            context.get("template_params")
                        )
                    else:
                        # Отправляем как обычное сообщение
                        success = await self.send_message(phone_number, message_text, context)

                    if success:
                        # Удаляем сообщение после успешной отправки
                        await self.message_repository.mark_pending_message_as_sent(message_id,
                                                                                   "resent_successfully")
                        logger.info(f"Successfully resent pending message: {message_id}")
                    else:
                        # Увеличиваем счетчик попыток
                        await self.message_repository.update_pending_message_attempts(message_id)

                    # Небольшая задержка между сообщениями
                    await asyncio.sleep(1)

                # Задержка между пользователями
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error resending pending messages: {str(e)}")

    async def _schedule_resend_pending_messages(self):
        """Запускает периодическую задачу для отправки отложенных сообщений"""
        try:
            while True:
                # Ждем указанное время
                await asyncio.sleep(self.retry_interval_seconds)

                # Запускаем отправку
                logger.info("Starting scheduled resend of pending messages")
                await self._resend_all_pending_messages()

        except asyncio.CancelledError:
            logger.info("Scheduled resend task cancelled")
        except Exception as e:
            logger.error(f"Error in scheduled resend task: {str(e)}")
            # Перезапускаем задачу после ошибки
            asyncio.create_task(self._schedule_resend_pending_messages())
