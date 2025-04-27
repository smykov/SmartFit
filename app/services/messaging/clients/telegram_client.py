# app/services/messaging/clients/telegram_client.py
import asyncio
from typing import Optional, Dict, Any
import logging
from telegram import Bot
from telegram.ext import Application

from app.services.messaging.interfaces.message_client_interface import IMessageClient
from app.services.localization.localization_interface import ILocalizationService
from app.services.messaging.messengers.telegram_messenger import TelegramMessenger

logger = logging.getLogger(__name__)


class TelegramClient(IMessageClient):
    """
    Клиент для отправки сообщений через Telegram Bot API
    Ответственность: Низкоуровневое взаимодействие с API Telegram
    """

    def __init__(self, token: str, localization_service: ILocalizationService, telegram_messenger: TelegramMessenger):
        """
        Инициализация клиента Telegram

        Args:
            token: Токен Telegram Bot API
            localization_service: Сервис локализации для сообщений
            telegram_messenger: Мессенджер для форматирования сообщений
        """
        self.bot = Bot(token=token)
        # Увеличиваем пул соединений
        application_builder = Application.builder().token(token)

        # Установка конфигурации пула соединений
        application_builder.connection_pool_size(16)  # Увеличиваем с дефолтных 4
        application_builder.pool_timeout(30.0)  # Увеличиваем таймаут

        self.application = application_builder.build()
        self.localization_service = localization_service
        self.telegram_messenger = telegram_messenger
        self.logger = logging.getLogger(self.__class__.__name__)

    async def send_message(self, to: str, message: str) -> Optional[str]:
        """
        Отправляет сообщение через Telegram Bot API

        Args:
            to: ID чата получателя
            message: Текст сообщения

        Returns:
            Optional[str]: ID отправленного сообщения или None в случае ошибки
        """
        try:
            # Проверяем, что сообщение не пустое
            if not message or not message.strip():
                self.logger.error("Empty message text, cannot send")
                return None

            # Форматируем сообщение для Telegram
            formatted_message = self.telegram_messenger.format_outgoing_message(message)
            try:
                result = await self.bot.send_message(
                    chat_id=to,
                    text=formatted_message,
                    parse_mode='Markdown'
                )
            except Exception as telegram_error:
                # При ошибке пробуем отправить без форматирования
                self.logger.warning(f"Error with Markdown formatting: {telegram_error} for message '{formatted_message}' Trying plain text '{message}'.")
                result = await self.bot.send_message(chat_id=to, text=message, parse_mode=None)

            await asyncio.sleep(1)

            return str(result.message_id)
        except Exception as e:
            self.logger.error(f"Error sending message via Telegram: {str(e)}")
            return None

    async def send_template_message(self, to: str, template_name: str, lang: Optional[str] = None,
                                    params: Dict[str, Any] = None) -> Optional[str]:
        """
        Отправляет локализованное шаблонное сообщение через Telegram

        Args:
            to: ID чата получателя
            template_name: Ключ шаблона сообщения
            lang: Код языка (если None, будет определен автоматически)
            params: Параметры для подстановки в шаблон

        Returns:
            Optional[str]: ID отправленного сообщения или None в случае ошибки
        """
        try:
            # Получаем текст шаблона через сервис локализации
            message_text = self.localization_service.get_message(template_name, lang, **(params or {}))

            self.logger.info(f"Sending template '{template_name}' for lang '{lang}' message: {message_text}")

            # Проверяем, что текст не пустой
            if not message_text or not message_text.strip():
                self.logger.error(f"Empty message text for template '{template_name}', language '{lang}'")
                return None

            # Отправляем сообщение
            return await self.send_message(to, message_text)
        except Exception as e:
            self.logger.error(f"Error sending template message: {str(e)}")
            return None