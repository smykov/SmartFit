import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.messaging.whatsapp_service import WhatsAppService


class TestWhatsAppService:
    """Тесты для WhatsAppService"""

    @pytest.fixture
    def mock_message_client(self):
        """Mock для IMessageClient"""
        client = AsyncMock()
        # Настраиваем возвращаемые значения
        client.send_message.return_value = "mock_message_id"
        client.send_template_message.return_value = "mock_template_id"
        return client

    @pytest.fixture
    def mock_message_repository(self):
        """Mock для IMessageRepository"""
        repository = AsyncMock()
        repository.find_pending_messages.return_value = []
        return repository

    @pytest.fixture
    def mock_text_splitter(self):
        """Mock для TextSplitter"""
        splitter = MagicMock()
        splitter.split_text.return_value = ["Part 1", "Part 2"]
        return splitter

    @pytest.fixture
    def whatsapp_service(self, mock_message_client, mock_message_repository, mock_text_splitter):
        """Создаёт экземпляр WhatsAppService для тестов"""
        return WhatsAppService(
            message_client=mock_message_client,
            message_repository=mock_message_repository,
            text_splitter=mock_text_splitter,
            from_phone_number="+123456789",
            retry_interval_seconds=60,
            max_message_size=100,
            max_message_age_hours=24
        )

    @pytest.mark.asyncio
    async def test_send_message_success(self, whatsapp_service, mock_message_client, mock_message_repository):
        """Тест успешной отправки сообщения"""
        # Arrange
        to_phone = "+987654321"
        message = "Test message"
        context = {"test": "value"}

        # Act
        result = await whatsapp_service.send_message(to_phone, message, context)

        # Assert
        assert result is True
        mock_message_client.send_message.assert_called_once_with(to_phone, message)
        mock_message_repository.save_sent_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_failure(self, whatsapp_service, mock_message_client, mock_message_repository):
        """Тест неудачной отправки сообщения"""
        # Arrange
        to_phone = "+987654321"
        message = "Test message"
        context = {"test": "value"}
        mock_message_client.send_message.return_value = None

        # Act
        result = await whatsapp_service.send_message(to_phone, message, context)

        # Assert
        assert result is False
        mock_message_client.send_message.assert_called_once_with(to_phone, message)
        mock_message_repository.save_pending_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_chunked_message(self, whatsapp_service, mock_text_splitter):
        """Тест отправки разбитого на части сообщения"""
        # Arrange
        to_phone = "+987654321"
        message = "Long test message that needs to be split"
        whatsapp_service.send_message = AsyncMock(return_value=True)

        # Act
        result = await whatsapp_service.send_chunked_message(to_phone, message)

        # Assert
        assert result is True
        assert mock_text_splitter.split_text.called
        assert whatsapp_service.send_message.call_count == 2  # Вызов для каждой части

    @pytest.mark.asyncio
    async def test_send_template_message(self, whatsapp_service, mock_message_client, mock_message_repository):
        """Тест отправки шаблонного сообщения"""
        # Arrange
        to_phone = "+987654321"
        template_name = "welcome"
        params = ["param1", "param2"]

        # Act
        result = await whatsapp_service.send_template_message(to_phone, template_name, params)

        # Assert
        assert result is True
        mock_message_client.send_template_message.assert_called_once_with(to_phone, template_name, params)
        mock_message_repository.save_sent_message.assert_called_once()