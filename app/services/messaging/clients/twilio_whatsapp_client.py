import logging
from typing import Optional, Dict, Any, List

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from app.services.messaging.interfaces.message_client_interface import IMessageClient

logger = logging.getLogger(__name__)


class TwilioWhatsAppClient(IMessageClient):
    """
    Клиент для отправки сообщений через Twilio WhatsApp API
    """

    def __init__(self, account_sid: str, auth_token: str, from_phone: str):
        """
        Инициализация клиента Twilio

        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_phone: Номер телефона отправителя
        """
        self.client = Client(account_sid, auth_token)
        self.from_phone = from_phone

    async def send_message(self, to: str, message: str) -> Optional[str]:
        """
        Отправляет сообщение через Twilio WhatsApp API

        Args:
            to: Номер телефона получателя
            message: Текст сообщения

        Returns:
            Optional[str]: ID отправленного сообщения или None в случае ошибки
        """
        try:
            # Нормализуем номер телефона
            to_number = self._normalize_phone_number(to)
            from_number = f"whatsapp:{self.from_phone}"
            to_number = f"whatsapp:{to_number}"

            # Отправляем сообщение
            message_response = self.client.messages.create(
                from_=from_number,
                body=message,
                to=to_number
            )

            # Возвращаем ID сообщения
            return message_response.sid

        except TwilioRestException as e:
            # Логируем ошибку Twilio
            error_code = e.status if hasattr(e, 'status') else 'unknown'
            logger.error(f"Twilio error ({error_code}): {str(e)}")
            return None

        except Exception as e:
            # Общая обработка ошибок
            logger.error(f"Error sending message via Twilio: {str(e)}")
            return None

    async def send_template_message(self, to: str, template_name: str, params: List[Any] = None) -> Optional[str]:
        """
        Отправляет шаблонное сообщение через Twilio WhatsApp API

        Args:
            to: Номер телефона получателя
            template_name: Имя шаблона
            params: Параметры для шаблона

        Returns:
            Optional[str]: ID отправленного сообщения или None в случае ошибки
        """
        try:
            # Нормализуем номер телефона
            to_number = self._normalize_phone_number(to)
            from_number = f"whatsapp:{self.from_phone}"
            to_number = f"whatsapp:{to_number}"

            # Формируем содержимое шаблона
            # Для Twilio это просто текст, поскольку API шаблонов ограничено
            message_body = self._format_template(template_name, params)

            # Отправляем сообщение
            message_response = self.client.messages.create(
                from_=from_number,
                body=message_body,
                to=to_number
            )

            # Возвращаем ID сообщения
            return message_response.sid

        except TwilioRestException as e:
            # Логируем ошибку Twilio
            logger.error(f"Twilio template message error: {str(e)}")
            return None

        except Exception as e:
            # Общая обработка ошибок
            logger.error(f"Error sending template message via Twilio: {str(e)}")
            return None

    def _normalize_phone_number(self, phone_number: str) -> str:
        """
        Нормализует номер телефона

        Args:
            phone_number: Номер телефона

        Returns:
            str: Нормализованный номер телефона
        """
        # Удаляем символы "whatsapp:" если они есть
        if phone_number.startswith("whatsapp:"):
            phone_number = phone_number[9:]

        # Добавляем префикс "+" если его нет
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"

        return phone_number

    def _format_template(self, template_name: str, params: List[Any] = None) -> str:
        """
        Форматирует шаблон сообщения

        Args:
            template_name: Имя шаблона
            params: Параметры для шаблона

        Returns:
            str: Форматированный текст шаблона
        """
        # Для реализации можно использовать локализованные сообщения
        # или более сложную систему шаблонов

        # Заглушка для примера
        templates = {
            "welcome": "👋 Привет! Добро пожаловать в GuateFit - твой персональный ассистент.",
            "diet_created": "🎉 Твой план питания готов!",
            "weight_reminder": "⚖️ Не забудь записать свой вес сегодня."
        }

        # Берем базовый шаблон
        message_text = templates.get(template_name, "")

        # Заменяем параметры
        if params:
            for i, param in enumerate(params):
                message_text = message_text.replace(f"{{{i}}}", str(param))

        return message_text