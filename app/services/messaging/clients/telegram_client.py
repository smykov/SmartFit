from typing import Optional, Dict, Any
import logging
from telegram import Bot
from telegram.ext import Application

from app.services.messaging.interfaces.message_client_interface import IMessageClient
from app.services.localization.localization_interface import ILocalizationService

logger = logging.getLogger(__name__)


class TelegramClient(IMessageClient):
    """Клиент для отправки сообщений через Telegram Bot API"""

    def __init__(self, token: str, localization_service: ILocalizationService):
        """
        Инициализация клиента Telegram

        Args:
            token: Токен Telegram Bot API
            localization_service: Сервис локализации для сообщений
        """
        self.bot = Bot(token=token)
        self.application = Application.builder().token(token).build()
        self.localization_service = localization_service

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
            result = await self.bot.send_message(chat_id=to, text=message, parse_mode='MarkdownV2')
            return str(result.message_id)
        except Exception as e:
            logger.error(f"Error sending message via Telegram: {str(e)}")
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

            # Отправляем сообщение
            return await self.send_message(to, message_text)
        except Exception as e:
            logger.error(f"Error sending template message: {str(e)}")
            return None