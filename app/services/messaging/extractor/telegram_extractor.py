from typing import Dict, Any, Tuple, Optional

from app.models.messaging import MessageType
from app.services.messaging.extractor.message_extractor import MessageExtractor
from main import logger


class TelegramExtractor(MessageExtractor):
    """Стратегия извлечения данных из сообщений Telegram"""

    def extract_message_data(self, body: Dict[str, Any]) -> Tuple[
        Optional[str], Optional[str], Optional[str], Optional[str]]:
        try:
            if 'message' not in body:
                return None, None, None, None

            message = body['message']
            chat_id = str(message.get('chat', {}).get('id', ''))
            message_text = message.get('text', '')
            message_type = MessageType.TEXT  # По умолчанию текстовое сообщение
            message_id = str(message.get('message_id', ''))

            # Проверяем, есть ли фото или другие типы сообщений
            if 'photo' in message:
                message_type = MessageType.MEDIA

            return chat_id, message_text, message_type, message_id

        except Exception as e:
            logger.error(f"Error extracting Telegram message data: {str(e)}")
            return None, None, None, None