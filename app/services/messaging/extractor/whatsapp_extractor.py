from typing import Dict, Any, Tuple, Optional

from app.models.messaging import MessageType
from app.services.messaging.extractor.message_extractor import MessageExtractor
from main import logger


class WhatsAppExtractor(MessageExtractor):
    """Стратегия извлечения данных из сообщений WhatsApp"""

    def extract_message_data(self, body: Dict[str, Any]) -> Tuple[
        Optional[str], Optional[str], Optional[str], Optional[str]]:
        try:
            phone_number = body.get("From", "").replace("whatsapp:", "")
            message_text = body.get("Body", "")
            message_type = MessageType.TEXT  # По умолчанию текстовое сообщение
            message_id = body.get("MessageSid", "") or body.get("SmsMessageSid", "")

            # Проверяем, есть ли медиа в сообщении
            if "MediaUrl0" in body:
                message_type = MessageType.MEDIA

            return phone_number, message_text, message_type, message_id

        except Exception as e:
            logger.error(f"Error extracting WhatsApp message data: {str(e)}")
            return None, None, None, None