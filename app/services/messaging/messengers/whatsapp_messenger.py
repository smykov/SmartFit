# app/services/messaging/messengers/whatsapp_messenger.py
from typing import Dict, Any, Optional

from app.services.localization.localization_interface import ILocalizationService
from app.services.messaging.messengers.messenger_base import MessengerBase


class WhatsAppMessenger(MessengerBase):
    """
    Мессенджер для WhatsApp
    Ответственность: Парсинг и форматирование сообщений для WhatsApp
    """

    def __init__(self, localization_service: ILocalizationService):
        """
        Инициализация мессенджера WhatsApp

        Args:
            localization_service: Сервис локализации
        """
        super().__init__(localization_service)

    async def parse_incoming_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Парсит входящее сообщение WhatsApp

        Args:
            data: Данные входящего сообщения

        Returns:
            Dict[str, Any]: Стандартизированное представление сообщения
        """
        try:
            return {
                "messenger_type": "whatsapp",
                "sender_id": data.get("From", "").replace("whatsapp:", ""),
                "message_text": data.get("Body", ""),
                "message_id": data.get("MessageSid", "") or data.get("SmsMessageSid", ""),
                "message_type": "text" if "MediaUrl0" not in data else "media",
                "raw_data": data
            }
        except Exception as e:
            self.logger.error(f"Error parsing WhatsApp message: {str(e)}")
            return {}

    def format_outgoing_message(self, message: str) -> str:
        """
        Форматирует исходящее сообщение для WhatsApp

        Args:
            message: Исходный текст сообщения

        Returns:
            str: Отформатированное сообщение для WhatsApp
        """
        # WhatsApp поддерживает простой Markdown: *bold*, _italic_, ~strikethrough~, ```code```
        return message

    def get_messenger_type(self) -> str:
        """
        Возвращает тип мессенджера

        Returns:
            str: "whatsapp"
        """
        return "whatsapp"
