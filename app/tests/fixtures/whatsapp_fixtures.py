import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from typing import Dict, Any, List, Optional

from app.services.messaging.clients.twilio_whatsapp_client import TwilioWhatsAppClient
from app.services.messaging.whatsapp_service import WhatsAppService


@pytest.fixture
def whatsapp_client_mock():
    """Возвращает мок для клиента WhatsApp API."""
    mock = MagicMock(spec=TwilioWhatsAppClient)

    # Список отправленных сообщений для отслеживания
    sent_messages = []
    template_messages = []

    # Методы для работы с сообщениями
    async def send_message(to, message, context=None):
        message_id = f"msg-{uuid.uuid4()}"
        sent_message = {
            "id": message_id,
            "to": to,
            "message": message,
            "context": context or {},
            "type": "text"
        }
        sent_messages.append(sent_message)
        return message_id

    async def send_template_message(to, template_name, lang=None, params=None):
        message_id = f"tmpl-{uuid.uuid4()}"
        template_message = {
            "id": message_id,
            "to": to,
            "template_name": template_name,
            "language": lang or "en",
            "params": params or {},
            "type": "template"
        }
        template_messages.append(template_message)
        return message_id

    # Привязываем методы к моку
    mock.send_message = AsyncMock(side_effect=send_message)
    mock.send_template_message = AsyncMock(side_effect=send_template_message)

    # Добавляем методы для доступа к отправленным сообщениям
    mock.get_sent_messages = lambda: sent_messages
    mock.get_template_messages = lambda: template_messages
    mock.clear_messages = lambda: (sent_messages.clear(), template_messages.clear())

    return mock


@pytest.fixture
def whatsapp_service_mock(whatsapp_client_mock, firebase_repositories):
    """Возвращает мок для сервиса WhatsApp."""
    from app.services.messaging.message_interface import IMessageService

    # Используем репозиторий сообщений
    message_repository = firebase_repositories["message_repository"]

    # Создаем мок сервиса
    mock = MagicMock(spec=IMessageService)

    # Методы для работы с сообщениями
    async def send_message(to_phone, message, context=None):
        return await whatsapp_client_mock.send_message(to_phone, message, context)

    async def send_messages(to_phone, messages):
        results = []
        for message in messages:
            result = await whatsapp_client_mock.send_message(to_phone, message)
            results.append(result)
        return all(results)

    async def send_template_message(to_phone, template_name, user_id=None, params=None):
        return await whatsapp_client_mock.send_template_message(to_phone, template_name, None, params)

    async def can_send_reminder(phone_number, reminder_type, min_interval_seconds):
        return True

    async def record_reminder_sent(phone_number, reminder_type):
        return True

    # Привязываем методы к моку
    mock.send_message = AsyncMock(side_effect=send_message)
    mock.send_messages = AsyncMock(side_effect=send_messages)
    mock.send_template_message = AsyncMock(side_effect=send_template_message)
    mock.can_send_reminder = AsyncMock(side_effect=can_send_reminder)
    mock.record_reminder_sent = AsyncMock(side_effect=record_reminder_sent)

    # Добавляем геттеры для доступа к отправленным сообщениям
    mock.get_sent_messages = whatsapp_client_mock.get_sent_messages
    mock.get_template_messages = whatsapp_client_mock.get_template_messages
    mock.clear_messages = whatsapp_client_mock.clear_messages

    return mock


@pytest.fixture
def real_whatsapp_service(whatsapp_client_mock, firebase_repositories):
    """Создает реальный экземпляр WhatsAppService с мок-зависимостями."""
    from app.utils.text_splitter import TextSplitter

    text_splitter = TextSplitter()

    # Создаем экземпляр сервиса
    service = WhatsAppService(
        message_client=whatsapp_client_mock,
        message_repository=firebase_repositories["message_repository"],
        localization_service=None,  # Будет добавлен позже
        text_splitter=text_splitter,
        from_phone_number="+1234567890",
        retry_interval_seconds=300,
        max_message_size=1500,
        max_message_age_hours=72
    )

    return service