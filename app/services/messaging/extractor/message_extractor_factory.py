from app.services.messaging.extractor.message_extractor import MessageExtractor
from app.services.messaging.extractor.telegram_extractor import TelegramExtractor
from app.services.messaging.extractor.whatsapp_extractor import WhatsAppExtractor


class MessageExtractorFactory:
    """Фабрика для создания экстракторов сообщений"""

    @staticmethod
    def create_extractor(messenger_type: str) -> MessageExtractor:
        """
        Создает экстрактор сообщений для указанного мессенджера

        Args:
            messenger_type: Тип мессенджера

        Returns:
            MessageExtractor: Экстрактор сообщений
        """
        if messenger_type.lower() == 'whatsapp':
            return WhatsAppExtractor()
        else:
            return TelegramExtractor() # По умолчанию telegram
