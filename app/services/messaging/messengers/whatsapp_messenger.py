# app/services/messaging/messengers/whatsapp_messenger.py
from typing import Dict, Any, Optional

from app.services.messaging.message_interface import IMessageService
from app.services.messaging.messengers.base_messenger import BaseMessenger
from app.services.messaging.clients.twilio_whatsapp_client import TwilioWhatsAppClient
from app.db.interfaces.message_repository_interface import IMessageRepository
from app.services.localization.localization_interface import ILocalizationService
from app.utils.text_splitter import TextSplitter


class WhatsAppMessenger(BaseMessenger):
    """
    Реализация мессенджера для WhatsApp
    """

    def __init__(self,
                 service: IMessageService,
                 message_repository: IMessageRepository,
                 localization_service: ILocalizationService,
                 text_splitter: TextSplitter,
                 from_phone_number: str,
                 max_message_size: int = 1500):
        super().__init__(message_repository, localization_service)
        self.service = service
        self.text_splitter = text_splitter
        self.from_phone_number = from_phone_number
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

        # Форматируем сообщение для WhatsApp
        formatted_message = self.format_outgoing_message(message)

        # Отправляем сообщение через клиент
        message_id = await self.service.send_message(recipient_id, formatted_message)

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
                                    user_id: Optional[str] = None,
                                    params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Отправка шаблонного сообщения"""
        # Логика отправки шаблонного сообщения...
        pass

    def get_messenger_type(self) -> str:
        """Получение типа мессенджера"""
        return "whatsapp"

    def parse_incoming_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Парсинг входящего сообщения"""
        # Логика извлечения данных из входящего сообщения WhatsApp...
        try:
            return {
                "messenger_type": "whatsapp",
                "sender_id": data.get("From", "").replace("whatsapp:", ""),
                "message_text": data.get("Body", ""),
                "message_id": data.get("MessageSid", ""),
                "message_type": "text" if "MediaUrl0" not in data else "media",
                "raw_data": data
            }
        except Exception as e:
            self.logger.error(f"Error parsing WhatsApp message: {str(e)}")
            return {}

    def format_outgoing_message(self, message: str) -> str:
        """Форматирование исходящего сообщения для WhatsApp"""
        # Базовое форматирование для WhatsApp...
        # WhatsApp поддерживает простой Markdown: *bold*, _italic_, ~strikethrough~, ```code```
        return message