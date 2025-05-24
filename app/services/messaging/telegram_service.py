import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import pytz
from telegram import Bot
from telegram.ext import Application

from app.constants.localization_keys import LocalizationKeys as LK
from app.db.interfaces.message_repository_interface import IMessageRepository
from app.services.messaging.interfaces.message_client_interface import IMessageClient
from app.services.localization.localization_interface import ILocalizationService
from app.services.messaging.interfaces.message_interface import IMessengerService
from app.utils.text_splitter import TextSplitter
from config import settings

logger = logging.getLogger(__name__)


class TelegramService(IMessengerService):
    """Сервис для работы с Telegram Bot API"""

    def __init__(
            self,
            message_client: IMessageClient,
            message_repository: IMessageRepository,
            localization_service: ILocalizationService,
            text_splitter: TextSplitter,
            bot_token: str,
            retry_interval_seconds: int = 300,
            max_message_size: int = 4000,
            max_message_age_hours: int = 72
    ):
        """
        Инициализация сервиса Telegram

        Args:
            message_client: Клиент для отправки сообщений
            message_repository: Репозиторий для работы с сообщениями
            localization_service: Сервис локализации сообщений
            text_splitter: Утилита для разбиения текста на части
            bot_token: Токен Telegram бота
            retry_interval_seconds: Интервал между повторными попытками отправки (в секундах)
            max_message_size: Максимальный размер сообщения
            max_message_age_hours: Максимальный возраст сообщений в часах
        """
        self.message_client = message_client
        self.message_repository = message_repository
        self.localization_service = localization_service
        self.text_splitter = text_splitter
        self.bot_token = bot_token
        self.retry_interval_seconds = retry_interval_seconds
        self.max_message_size = max_message_size
        self.max_message_age_hours = max_message_age_hours
        self.logger = logging.getLogger(self.__class__.__name__)

        # Специфичные для Telegram поля
        self.application = None

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
            logger.info("Initializing Telegram service...")

            # Настройка обработчиков Telegram
            self.application = Application.builder().token(self.bot_token).build()

            # Запускаем отправку отложенных сообщений
            await self._resend_all_pending_messages()

            # Запускаем периодическую задачу для отправки отложенных сообщений
            asyncio.create_task(self._schedule_resend_pending_messages())

            logger.info("Telegram service initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing Telegram service: {str(e)}")

    async def send_message(self, to_chat_id: str, message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет текстовое сообщение через Telegram

        Args:
            to_chat_id: ID чата получателя
            message: Текст сообщения
            context: Дополнительный контекст сообщения

        Returns:
            bool: Результат отправки
        """
        try:
            # Проверяем размер сообщения
            if len(message) > self.max_message_size:
                return await self.send_chunked_message(to_chat_id, message, context)

            # Отправляем сообщение через клиент
            message_id = await self.message_client.send_message(to_chat_id, message)

            if message_id:
                # Сохраняем информацию об отправленном сообщении
                await self.message_repository.save_sent_message(to_chat_id, message_id, message, context)
                logger.info(f"Message sent successfully to Telegram: {message_id}")
                return True
            else:
                # Сохраняем сообщение для повторной отправки
                error_type = "telegram_api_error"
                await self.message_repository.save_pending_message(to_chat_id, message, error_type, context)
                logger.warning(f"Failed to send message to Telegram chat {to_chat_id}, saved for retry")
                return False

        except Exception as e:
            logger.error(f"Error sending message via Telegram: {str(e)}")

            # Сохраняем сообщение для повторной отправки
            await self.message_repository.save_pending_message(to_chat_id, message, "general_error", context)
            return False

    async def send_chunked_message(self, to_chat_id: str, message: str,
                                   context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Разбивает длинное сообщение на части и отправляет последовательно

        Args:
            to_chat_id: ID чата получателя
            message: Текст сообщения
            context: Дополнительный контекст сообщения

        Returns:
            bool: Результат отправки (True, если все части отправлены успешно)
        """
        try:
            # Разбиваем сообщение на части с учетом ограничений Telegram
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
                part_success = await self.send_message(to_chat_id, full_part, part_context)
                success = success and part_success

                # Небольшая задержка между отправками
                await asyncio.sleep(0.5)

            return success

        except Exception as e:
            logger.error(f"Error sending chunked message via Telegram: {str(e)}")

            # Сохраняем сообщение для повторной отправки, но только первую часть
            await self.message_repository.save_pending_message(
                to_chat_id,
                message[:self.max_message_size] + "...",
                "chunking_error",
                context
            )

            return False

    async def send_messages(self, to_chat_id: str, messages: List[str],
                            context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет несколько текстовых сообщений последовательно

        Args:
            to_chat_id: ID чата получателя
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
                message_success = await self.send_message(to_chat_id, message, message_context)
                success = success and message_success

                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.5)

            return success

        except Exception as e:
            logger.error(f"Error sending multiple messages via Telegram: {str(e)}")
            return False

    async def send_template_message(self, to_chat_id: str, template_name: str, user_id: Optional[str] = None,
                                    params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет локализованное шаблонное сообщение через Telegram

        Args:
            to_chat_id: ID чата получателя
            template_name: Ключ шаблона сообщения
            user_id: ID пользователя для определения языка
            params: Параметры для подстановки в шаблон

        Returns:
            bool: Результат отправки
        """
        try:
            # Определяем язык пользователя, если предоставлен ID
            lang = None
            if user_id and self.localization_service:
                lang = await self.localization_service.get_user_language(user_id)

            # Отправляем шаблонное сообщение через клиент
            message_id = await self.message_client.send_template_message(
                to_chat_id,
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
                    to_chat_id,
                    message_id,
                    f"Template: {template_name}",
                    template_context
                )

                logger.info(f"Template message sent successfully via Telegram: {message_id}")
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
                    to_chat_id,
                    f"Template: {template_name}",
                    error_type,
                    template_context
                )

                logger.warning(f"Failed to send template message to Telegram chat {to_chat_id}, saved for retry")
                return False

        except Exception as e:
            logger.error(f"Error sending template message via Telegram: {str(e)}")
            return False

    async def can_send_reminder(self, chat_id: str, reminder_type: str, min_interval_seconds: int) -> bool:
        """
        Проверяет, можно ли отправить напоминание определенного типа

        Args:
            chat_id: ID чата пользователя
            reminder_type: Тип напоминания
            min_interval_seconds: Минимальный интервал между напоминаниями в секундах

        Returns:
            bool: True, если можно отправить напоминание
        """
        try:
            # Проверяем последнее отправленное напоминание этого типа
            # Note: Необходимо адаптировать reminder_repository для поддержки Telegram
            last_reminder = await self.reminder_repository.get_last_reminder(chat_id, reminder_type)

            if not last_reminder:
                return True

            # Проверяем, прошло ли достаточное количество времени
            current_time = DateHelper.get_current_datetime()
            reminder_time = datetime.fromisoformat(last_reminder.get("created_at", ""))

            seconds_since_last_reminder = (current_time - reminder_time).total_seconds()

            return seconds_since_last_reminder >= min_interval_seconds

        except Exception as e:
            logger.error(f"Error checking reminder eligibility: {str(e)}")
            return False

    async def record_reminder_sent(self, chat_id: str, reminder_type: str) -> None:
        """
        Записывает информацию об отправленном напоминании

        Args:
            chat_id: ID чата пользователя
            reminder_type: Тип напоминания
        """
        try:
            # Note: Необходимо адаптировать reminder_repository для поддержки Telegram
            await self.reminder_repository.save_reminder(chat_id, reminder_type)
        except Exception as e:
            logger.error(f"Error recording reminder: {str(e)}")

    async def _resend_all_pending_messages(self):
        """Отправляет все неотправленные сообщения для Telegram"""
        try:
            # Получаем неотправленные сообщения для Telegram
            # Note: Необходимо адаптировать message_repository для поддержки разных мессенджеров
            pending_messages = await self.message_repository.find_pending_messages(self.max_message_age_hours)

            # Фильтруем только сообщения для Telegram (по формату получателя - chat_id)
            telegram_messages = [msg for msg in pending_messages if
                                 self._is_telegram_recipient(msg.get("phone_number"))]

            if not telegram_messages:
                logger.info("No pending Telegram messages found to resend")
                return

            logger.info(f"Found {len(telegram_messages)} pending Telegram messages to resend")

            # Группируем сообщения по ID чата для более эффективной отправки
            messages_by_chat = {}

            for message in telegram_messages:
                chat_id = message.get("phone_number")
                if chat_id not in messages_by_chat:
                    messages_by_chat[chat_id] = []
                messages_by_chat[chat_id].append(message)

            # Обрабатываем сообщения для каждого чата
            for chat_id, messages in messages_by_chat.items():
                # Сортируем по времени (от ранних к поздним)
                sorted_messages = sorted(messages, key=lambda x: x.get("timestamp", ""))

                # Ограничиваем количество отправляемых сообщений
                for message in sorted_messages[:5]:  # Не более 5 сообщений за раз
                    # Проверяем, не устарело ли сообщение
                    timestamp = datetime.fromisoformat(message.get("timestamp", ""))
                    now = DateHelper.get_current_datetime()

                    if (now - timestamp).total_seconds() > self.max_message_age_hours * 3600:
                        # Помечаем как устаревшее
                        await self.message_repository.mark_pending_message_as_expired(message.get("id"))
                        logger.info(f"Marked expired Telegram message: {message.get('id')}")
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
                        message_text = f"{self.get_localized_message(LK.Messaging.DELAYED_MESSAGE)}\n\n{message_text}"

                    # Проверяем, является ли это шаблонным сообщением
                    if "template_name" in context:
                        # Отправляем как шаблонное сообщение
                        success = await self.send_template_message(
                            chat_id,
                            context["template_name"],
                            context.get("user_id"),
                            context.get("template_params")
                        )
                    else:
                        # Отправляем как обычное сообщение
                        success = await self.send_message(chat_id, message_text, context)

                    if success:
                        # Удаляем сообщение после успешной отправки
                        await self.message_repository.mark_pending_message_as_sent(message_id,
                                                                                   "resent_successfully")
                        logger.info(f"Successfully resent pending Telegram message: {message_id}")
                    else:
                        # Увеличиваем счетчик попыток
                        await self.message_repository.update_pending_message_attempts(message_id)

                    # Небольшая задержка между сообщениями
                    await asyncio.sleep(1)

                # Задержка между пользователями
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error resending pending Telegram messages: {str(e)}")

    async def _schedule_resend_pending_messages(self):
        """Запускает периодическую задачу для отправки отложенных сообщений"""
        try:
            while True:
                # Ждем указанное время
                await asyncio.sleep(self.retry_interval_seconds)

                # Запускаем отправку
                logger.info("Starting scheduled resend of pending Telegram messages")
                await self._resend_all_pending_messages()

        except asyncio.CancelledError:
            logger.info("Scheduled Telegram resend task cancelled")
        except Exception as e:
            logger.error(f"Error in scheduled Telegram resend task: {str(e)}")
            # Перезапускаем задачу после ошибки
            asyncio.create_task(self._schedule_resend_pending_messages())

    def _is_telegram_recipient(self, recipient: str) -> bool:
        """
        Определяет, является ли получатель пользователем Telegram

        Args:
            recipient: Идентификатор получателя

        Returns:
            bool: True, если получатель из Telegram
        """
        # В Telegram chat_id обычно числовые и начинаются с "-" для групповых чатов
        # или не содержат специальных символов для приватных чатов
        if not recipient:
            return False

        # Простая эвристика: если в строке нет "+", вероятно это Telegram chat_id, а не номер телефона
        if "+" not in recipient and not recipient.startswith("whatsapp:"):
            return True

        return False