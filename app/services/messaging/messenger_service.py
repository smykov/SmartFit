# app/services/messaging/messenger_service.py
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import pytz

from app.constants.localization_keys import LocalizationKeys as LK
from app.db.interfaces.message_repository_interface import IMessageRepository
from app.db.interfaces.reminder_repository_interface import IReminderRepository
from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.localization.localization_interface import ILocalizationService
from app.services.messaging.interfaces.message_client_interface import IMessageClient
from app.services.messaging.interfaces.message_interface import IMessengerService
from app.services.messaging.messenger_registry import MessengerRegistry
from app.utils.text_splitter import TextSplitter
from config import settings


class MessengerService(IMessengerService):
    """
    Единый сервис для работы с разными мессенджерами
    Ответственность: Фасад и бизнес-логика работы с сообщениями
    """

    def __init__(
            self,
            messenger_registry: MessengerRegistry,
            message_repository: IMessageRepository,
            reminder_repository: IReminderRepository,
            user_repository: IUserRepository,
            localization_service: ILocalizationService,
            text_splitter: TextSplitter,
            whatsapp_client: IMessageClient,
            telegram_client: IMessageClient,
            whatsapp_phone: str,
            retry_interval_seconds: int = 300,
            max_message_size_whatsapp: int = 1500,
            max_message_size_telegram: int = 4000,
            max_message_age_hours: int = 72
    ):
        """
        Инициализация сервиса мессенджеров

        Args:
            messenger_registry: Реестр мессенджеров
            message_repository: Репозиторий сообщений
            reminder_repository: Репозиторий напоминаний
            user_repository: Репозиторий пользователей
            localization_service: Сервис локализации
            text_splitter: Утилита для разбиения длинных сообщений
            whatsapp_client: Клиент WhatsApp API
            telegram_client: Клиент Telegram API
            whatsapp_phone: Номер телефона WhatsApp для отправки
            retry_interval_seconds: Интервал повторной отправки (секунды)
            max_message_size_whatsapp: Максимальный размер сообщения WhatsApp
            max_message_size_telegram: Максимальный размер сообщения Telegram
            max_message_age_hours: Максимальный возраст сообщений (часы)
        """
        self.messenger_registry = messenger_registry
        self.message_repository = message_repository
        self.reminder_repository = reminder_repository
        self.user_repository = user_repository
        self.localization_service = localization_service
        self.text_splitter = text_splitter

        self.whatsapp_client = whatsapp_client
        self.telegram_client = telegram_client
        self.whatsapp_phone = whatsapp_phone

        self.retry_interval_seconds = retry_interval_seconds
        self.max_message_size = {
            "whatsapp": max_message_size_whatsapp,
            "telegram": max_message_size_telegram,
        }
        self.max_message_age_hours = max_message_age_hours

        self.logger = logging.getLogger(self.__class__.__name__)

    def get_localized_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        """
        Получает локализованное сообщение из сервиса локализации

        Args:
            key: Ключ сообщения
            lang: Код языка (по умолчанию используется системный язык)
            **params: Параметры для форматирования

        Returns:
            str: Локализованное сообщение
        """
        if self.localization_service:
            return self.localization_service.get_message(key, lang, **params)
        return key

    async def initialize(self):
        """Инициализация сервиса и запуск регулярных задач"""
        try:
            self.logger.info("Initializing Messenger Service...")

            # Запускаем отправку отложенных сообщений
            await self._resend_all_pending_messages()

            # Запускаем периодическую задачу для отправки отложенных сообщений
            asyncio.create_task(self._schedule_resend_pending_messages())

            self.logger.info("Messenger Service initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing Messenger Service: {str(e)}")

    async def get_preferred_messenger_type(self, user_id: Optional[str],
                                           context: Optional[Dict[str, Any]] = None) -> str:
        """
        Определяет предпочитаемый тип мессенджера для пользователя

        Args:
            user_id: ID пользователя
            context: Контекст сообщения

        Returns:
            str: Тип мессенджера ("whatsapp" или "telegram")
        """
        # Если тип мессенджера указан в контексте, используем его
        if context and "messenger_type" in context:
            return context["messenger_type"]

        # Если указан ID пользователя, получаем его предпочтения
        if user_id:
            user = await self.user_repository.get_by_id(user_id)
            if user and "preferred_messenger" in user:
                return user["preferred_messenger"]

        # По умолчанию используем WhatsApp
        return "whatsapp"

    async def _get_message_client(self, messenger_type: str) -> IMessageClient:
        """
        Возвращает клиент для отправки сообщений по типу мессенджера

        Args:
            messenger_type: Тип мессенджера

        Returns:
            IMessageClient: Клиент мессенджера
        """
        if messenger_type.lower() == "telegram":
            return self.telegram_client
        return self.whatsapp_client

    def _get_max_message_size(self, messenger_type: str) -> int:
        """
        Возвращает максимальный размер сообщения для указанного типа мессенджера

        Args:
            messenger_type: Тип мессенджера

        Returns:
            int: Максимальный размер сообщения
        """
        return self.max_message_size.get(messenger_type.lower(), 1500)  # По умолчанию 1500

    async def send_message(self, recipient_id: str, message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет текстовое сообщение через соответствующий мессенджер

        Args:
            recipient_id: Идентификатор получателя
            message: Текст сообщения
            context: Дополнительный контекст сообщения

        Returns:
            bool: Результат отправки
        """
        try:
            context = context or {}

            # Определяем тип мессенджера
            user_id = context.get('user_id')
            messenger_type = await self.get_preferred_messenger_type(user_id, context)

            # Получаем мессенджер для форматирования
            messenger = self.messenger_registry.get_messenger(messenger_type)
            if not messenger:
                self.logger.error(f"Messenger '{messenger_type}' not found")
                return False

            # Форматируем сообщение
            formatted_message = messenger.format_outgoing_message(message)

            # Проверяем размер сообщения
            max_size = self._get_max_message_size(messenger_type)
            if len(formatted_message) > max_size:
                return await self._send_chunked_message(recipient_id, message, messenger_type, context)

            # Получаем клиент для отправки
            client = await self._get_message_client(messenger_type)

            # Отправляем сообщение
            message_id = await client.send_message(recipient_id, formatted_message)

            if message_id:
                # Сохраняем информацию об отправленном сообщении
                context['messenger_type'] = messenger_type
                await self.message_repository.save_sent_message(recipient_id, message_id, message, context)
                self.logger.info(f"Message sent successfully: {message_id}")
                return True
            else:
                # Сохраняем сообщение для повторной отправки
                error_type = f"{messenger_type}_api_error"
                context['messenger_type'] = messenger_type
                await self.message_repository.save_pending_message(recipient_id, message, error_type, context)
                self.logger.warning(f"Failed to send message to {recipient_id}, saved for retry")
                return False

        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")

            # Сохраняем сообщение для повторной отправки
            if context is None:
                context = {}
            context['error'] = str(e)
            await self.message_repository.save_pending_message(recipient_id, message, "general_error", context)

            return False

    async def _send_chunked_message(self, recipient_id: str, message: str, messenger_type: str,
                                    context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Разбивает длинное сообщение на части и отправляет последовательно

        Args:
            recipient_id: Идентификатор получателя
            message: Текст сообщения
            messenger_type: Тип мессенджера
            context: Дополнительный контекст сообщения

        Returns:
            bool: Результат отправки (True, если все части отправлены успешно)
        """
        try:
            context = context or {}
            max_size = self._get_max_message_size(messenger_type)

            # Получаем мессенджер для форматирования
            messenger = self.messenger_registry.get_messenger(messenger_type)
            if not messenger:
                self.logger.error(f"Messenger '{messenger_type}' not found")
                return False

            # Разбиваем сообщение на части с учетом максимального размера
            parts = self.text_splitter.split_text(message, max_size)

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
                part_context["messenger_type"] = messenger_type

                # Отправляем часть
                part_success = await self.send_message(recipient_id, full_part, part_context)
                success = success and part_success

                # Небольшая задержка между отправками
                await asyncio.sleep(0.5)

            return success

        except Exception as e:
            self.logger.error(f"Error sending chunked message: {str(e)}")

            # Сохраняем сообщение для повторной отправки, но только первую часть
            first_part = message[:self._get_max_message_size(messenger_type) - 3] + "..."
            context_with_error = context.copy() if context else {}
            context_with_error['error'] = str(e)
            context_with_error['messenger_type'] = messenger_type
            await self.message_repository.save_pending_message(
                recipient_id,
                first_part,
                "chunking_error",
                context_with_error
            )

            return False

    async def send_messages(self, recipient_id: str, messages: List[str],
                            context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет несколько текстовых сообщений последовательно

        Args:
            recipient_id: Идентификатор получателя
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
                message_success = await self.send_message(recipient_id, message, message_context)
                success = success and message_success

                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.5)

            return success

        except Exception as e:
            self.logger.error(f"Error sending multiple messages: {str(e)}")
            return False

    async def send_template_message(self, recipient_id: str, template_name: str, user_id: Optional[str] = None,
                                    params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет локализованное шаблонное сообщение

        Args:
            recipient_id: Идентификатор получателя
            template_name: Ключ шаблона сообщения
            user_id: ID пользователя для определения языка
            params: Параметры для подстановки в шаблон

        Returns:
            bool: Результат отправки
        """
        try:
            params = params or {}

            # Определяем тип мессенджера для пользователя
            context = {"user_id": user_id, "template_name": template_name}
            messenger_type = await self.get_preferred_messenger_type(user_id, context)

            # Определяем язык пользователя
            lang = None
            if user_id and self.localization_service:
                lang = await self.localization_service.get_user_language(user_id)

            # Получаем клиент для отправки
            client = await self._get_message_client(messenger_type)

            # Отправляем шаблонное сообщение через клиент
            message_id = await client.send_template_message(
                recipient_id,
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
                    "user_id": user_id,
                    "messenger_type": messenger_type
                }

                # Сохраняем информацию об отправленном сообщении
                await self.message_repository.save_sent_message(
                    recipient_id,
                    message_id,
                    f"Template: {template_name}",
                    template_context
                )

                self.logger.info(f"Template message sent successfully: {message_id}")
                return True
            else:
                # Сохраняем сообщение для повторной отправки
                error_type = "template_send_error"
                template_context = {
                    "template_name": template_name,
                    "template_params": params,
                    "language": lang,
                    "user_id": user_id,
                    "messenger_type": messenger_type
                }

                await self.message_repository.save_pending_message(
                    recipient_id,
                    f"Template: {template_name}",
                    error_type,
                    template_context
                )

                self.logger.warning(f"Failed to send template message to {recipient_id}, saved for retry")
                return False

        except Exception as e:
            self.logger.error(f"Error sending template message: {str(e)}")
            return False

    async def can_send_reminder(self, recipient_id: str, reminder_type: str, min_interval_seconds: int) -> bool:
        """
        Проверяет, можно ли отправить напоминание определенного типа

        Args:
            recipient_id: Идентификатор получателя
            reminder_type: Тип напоминания
            min_interval_seconds: Минимальный интервал между напоминаниями в секундах

        Returns:
            bool: True, если можно отправить напоминание
        """
        try:
            # Проверяем последнее отправленное напоминание этого типа
            last_reminder = await self.reminder_repository.get_last_reminder(recipient_id, reminder_type)

            if not last_reminder:
                return True

            # Проверяем, прошло ли достаточное количество времени
            current_time = datetime.now(pytz.timezone(settings.TIMEZONE))
            reminder_time = datetime.fromisoformat(last_reminder.get("created_at", ""))

            seconds_since_last_reminder = (current_time - reminder_time).total_seconds()

            return seconds_since_last_reminder >= min_interval_seconds

        except Exception as e:
            self.logger.error(f"Error checking reminder eligibility: {str(e)}")
            return False

    async def record_reminder_sent(self, recipient_id: str, reminder_type: str) -> None:
        """
        Записывает информацию об отправленном напоминании

        Args:
            recipient_id: Идентификатор получателя
            reminder_type: Тип напоминания
        """
        try:
            await self.reminder_repository.save_reminder(recipient_id, reminder_type)
        except Exception as e:
            self.logger.error(f"Error recording reminder: {str(e)}")

    async def _resend_all_pending_messages(self):
        """Отправляет все неотправленные сообщения"""
        try:
            # Получаем неотправленные сообщения
            pending_messages = await self.message_repository.find_pending_messages(self.max_message_age_hours)

            if not pending_messages:
                self.logger.info("No pending messages found to resend")
                return

            self.logger.info(f"Found {len(pending_messages)} pending messages to resend")

            # Группируем сообщения по получателю для более эффективной отправки
            messages_by_recipient = {}

            for message in pending_messages:
                recipient = message.get("phone_number")
                if recipient not in messages_by_recipient:
                    messages_by_recipient[recipient] = []
                messages_by_recipient[recipient].append(message)

            # Обрабатываем сообщения для каждого получателя
            for recipient_id, messages in messages_by_recipient.items():
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
                        self.logger.info(f"Marked expired message: {message.get('id')}")
                        continue

                    # Извлекаем данные сообщения
                    message_text = message.get("message_text", "")
                    message_id = message.get("id")

                    # Создаем контекст из существующих метаданных
                    context = {k: v for k, v in message.items() if k not in
                               ["id", "phone_number", "message_text", "status", "attempts",
                                "timestamp", "last_attempt", "error_type"]}

                    # Определяем тип мессенджера
                    messenger_type = context.get("messenger_type", "whatsapp")

                    # Добавляем префикс для старых сообщений
                    if (now - timestamp).total_seconds() > 3600:  # Старше 1 часа
                        message_text = f"{self.get_localized_message(LK.Messaging.DELAYED_MESSAGE)}\n\n{message_text}"

                    # Проверяем, является ли это шаблонным сообщением
                    if "template_name" in context:
                        # Отправляем как шаблонное сообщение
                        success = await self.send_template_message(
                            recipient_id,
                            context["template_name"],
                            context.get("user_id"),
                            context.get("template_params")
                        )
                    else:
                        # Отправляем как обычное сообщение
                        success = await self.send_message(recipient_id, message_text, context)

                    if success:
                        # Удаляем сообщение после успешной отправки
                        await self.message_repository.mark_pending_message_as_sent(message_id,
                                                                                   "resent_successfully")
                        self.logger.info(f"Successfully resent pending message: {message_id}")
                    else:
                        # Увеличиваем счетчик попыток
                        await self.message_repository.update_pending_message_attempts(message_id)

                    # Небольшая задержка между сообщениями
                    await asyncio.sleep(1)

                # Задержка между пользователями
                await asyncio.sleep(5)

        except Exception as e:
            self.logger.error(f"Error resending pending messages: {str(e)}")

    async def _schedule_resend_pending_messages(self):
        """Запускает периодическую задачу для отправки отложенных сообщений"""
        try:
            while True:
                # Ждем указанное время
                await asyncio.sleep(self.retry_interval_seconds)

                # Запускаем отправку
                self.logger.info("Starting scheduled resend of pending messages")
                await self._resend_all_pending_messages()

        except asyncio.CancelledError:
            self.logger.info("Scheduled resend task cancelled")
        except Exception as e:
            self.logger.error(f"Error in scheduled resend task: {str(e)}")
            # Перезапускаем задачу после ошибки
            asyncio.create_task(self._schedule_resend_pending_messages())
