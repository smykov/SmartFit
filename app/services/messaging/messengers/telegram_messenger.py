# app/services/messaging/messengers/telegram_messenger.py
from typing import Dict, Any, Optional
import re

from app.services.messaging.messengers.base_messenger import BaseMessenger
from app.services.messaging.clients.telegram_client import TelegramClient
from app.db.interfaces.message_repository_interface import IMessageRepository
from app.services.localization.localization_interface import ILocalizationService
from app.utils.text_splitter import TextSplitter


class TelegramMessenger(BaseMessenger):
    """
    Реализация мессенджера для Telegram
    """

    def __init__(self,
                 client: TelegramClient,
                 message_repository: IMessageRepository,
                 localization_service: ILocalizationService,
                 text_splitter: TextSplitter,
                 max_message_size: int = 4000):
        super().__init__(message_repository, localization_service)
        self.client = client
        self.text_splitter = text_splitter
        self.max_message_size = max_message_size

    async def initialize(self) -> bool:
        """Инициализация мессенджера"""
        # Логика инициализации...
        return True

    async def send_message(self, recipient_id: str, message: str,
                           context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Отправка сообщения"""
        # Проверяем размер сообщения
        if len(message) > self.max_message_size:
            return await self._send_chunked_message(recipient_id, message, context)

        # Форматируем сообщение для Telegram
        formatted_message = self.format_outgoing_message(message)

        # Отправляем сообщение через клиент
        message_id = await self.client.send_message(recipient_id, formatted_message)

        if message_id:
            # Сохраняем информацию об отправленном сообщении
            await self.message_repository.save_sent_message(
                recipient_id, message_id, message, context
            )
            return message_id
        return None

    async def _send_chunked_message(self, recipient_id: str, message: str,
                                    context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Отправка разбитого на части сообщения"""
        # Логика разбиения и отправки длинного сообщения...
        pass

    async def send_template_message(self, recipient_id: str, template_name: str,
                                    lang: Optional[str] = None,
                                    params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Отправка шаблонного сообщения"""
        return await self.client.send_template_message(recipient_id, template_name, lang, params)

    def get_messenger_type(self) -> str:
        """Получение типа мессенджера"""
        return "telegram"

    def parse_incoming_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Парсинг входящего сообщения"""
        # Логика извлечения данных из входящего сообщения Telegram...
        try:
            if 'message' not in data:
                return {}

            message = data['message']
            return {
                "messenger_type": "telegram",
                "sender_id": str(message.get('chat', {}).get('id', '')),
                "message_text": message.get('text', ''),
                "message_id": str(message.get('message_id', '')),
                "language_code": str(message.get('from', {}).get('language_code', "en")),
                "message_type": "text" if 'photo' not in message else "media",
                "raw_data": data
            }
        except Exception as e:
            self.logger.error(f"Error parsing Telegram message: {str(e)}")
            return {}

    def format_outgoing_message(self, message: str) -> str:
        """Форматирование исходящего сообщения для Telegram"""
        # В Telegram нужно экранировать специальные символы для MarkdownV2
        special_chars = '_*[]()~`>#+-=|{}.!'
        for char in special_chars:
            message = message.replace(char, f'\\{char}')
        return message
