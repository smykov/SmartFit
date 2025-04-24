# app/services/messaging/messengers/telegram_messenger.py
from typing import Dict, Any, Optional

from app.services.localization.localization_interface import ILocalizationService
from app.services.messaging.messengers.messenger_base import MessengerBase


class TelegramMessenger(MessengerBase):
    """
    Мессенджер для Telegram
    Ответственность: Парсинг и форматирование сообщений для Telegram
    """

    def __init__(self, localization_service: ILocalizationService):
        """
        Инициализация мессенджера Telegram

        Args:
            localization_service: Сервис локализации
        """
        super().__init__(localization_service)

    async def parse_incoming_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Парсит входящее сообщение Telegram

        Args:
            data: Данные входящего сообщения

        Returns:
            Dict[str, Any]: Стандартизированное представление сообщения
        """
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
        """
        Форматирует исходящее сообщение для Telegram

        Args:
            message: Исходный текст сообщения

        Returns:
            str: Отформатированное сообщение для Telegram (без экранирования)
        """
        # Для Telegram не используем специальное форматирование, отправляем как обычный текст
        # Это избавит от необходимости экранировать специальные символы
        return message

    def get_messenger_type(self) -> str:
        """
        Возвращает тип мессенджера

        Returns:
            str: "telegram"
        """
        return "telegram"
