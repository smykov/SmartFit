# tests/mocks/whatsapp/whatsapp_client_mock.py
from typing import Dict, Any, Optional, List
import uuid


class WhatsAppClientMock:
    """Мок для клиента WhatsApp API."""

    def __init__(self):
        """Инициализация мока с сохранением отправленных сообщений."""
        self.sent_messages = []
        self.template_messages = []

    async def send_message(self, to: str, message: str, context: Dict[str, Any] = None) -> Optional[str]:
        """Имитирует отправку сообщения через WhatsApp API."""
        message_id = f"mock-msg-{uuid.uuid4()}"

        sent_message = {
            "id": message_id,
            "to": to,
            "text": message,
            "context": context or {},
            "timestamp": "2023-01-01T12:00:00Z"
        }

        self.sent_messages.append(sent_message)
        return message_id

    async def send_template_message(self, to: str, template_name: str, lang: str = None,
                                    params: Dict[str, Any] = None) -> Optional[str]:
        """Имитирует отправку шаблонного сообщения через WhatsApp API."""
        message_id = f"mock-template-{uuid.uuid4()}"

        template_message = {
            "id": message_id,
            "to": to,
            "template_name": template_name,
            "language": lang or "en",
            "params": params or {},
            "timestamp": "2023-01-01T12:00:00Z"
        }

        self.template_messages.append(template_message)
        return message_id

    def get_sent_messages(self) -> List[Dict[str, Any]]:
        """Возвращает список отправленных сообщений."""
        return self.sent_messages

    def get_template_messages(self) -> List[Dict[str, Any]]:
        """Возвращает список отправленных шаблонных сообщений."""
        return self.template_messages

    def clear_messages(self) -> None:
        """Очищает список отправленных сообщений."""
        self.sent_messages = []
        self.template_messages = []