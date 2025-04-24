# app/services/messaging/clients/twilio_whatsapp_client.py
import logging
from typing import Optional, Dict, Any

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from app.services.localization.localization_interface import ILocalizationService
from app.services.messaging.interfaces.message_client_interface import IMessageClient

logger = logging.getLogger(__name__)


class TwilioWhatsAppClient(IMessageClient):
    """
    Клиент для отправки сообщений через Twilio WhatsApp API
    Ответственность: Низкоуровневое взаимодействие с API Twilio
    """

    def __init__(self, account_sid: str, auth_token: str, from_phone: str, localization_service: ILocalizationService):
        """
        Инициализация клиента Twilio

        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_phone: Номер телефона отправителя
            localization_service: Сервис локализации для сообщений
        """
        self.client = Client(account_sid, auth_token)
        self.from_phone = from_phone
        self.localization_service = localization_service
        self.logger = logging.getLogger(self.__class__.__name__)

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
            self.logger.error(f"Twilio error ({error_code}): {str(e)}")
            return None

        except Exception as e:
            # Общая обработка ошибок
            self.logger.error(f"Error sending message via Twilio: {str(e)}")
            return None

    async def send_template_message(self, to: str, template_name: str, lang: Optional[str] = None,
                                    params: Dict[str, Any] = None) -> Optional[str]:
        """
        Отправляет локализованное шаблонное сообщение

        Args:
            to: Номер телефона получателя
            template_name: Ключ шаблона в словаре локализаций
            lang: Код языка (если None, будет определен автоматически)
            params: Параметры для подстановки в шаблон

        Returns:
            Optional[str]: ID отправленного сообщения или None в случае ошибки
        """
        try:
            # Нормализуем номер телефона
            to_number = self._normalize_phone_number(to)

            # Получаем текст шаблона через сервис локализации
            message_text = self.localization_service.get_message(template_name, lang, **(params or {}))

            # Отправляем сообщение
            return await self.send_message(to_number, message_text)

        except Exception as e:
            self.logger.error(f"Error sending template ('{lang}.{template_name}') message: {str(e)}")
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
