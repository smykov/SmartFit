# app/services/messaging/interfaces/message_client_interface.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class IMessageClient(ABC):
    """
    Интерфейс для клиентов отправки сообщений (Twilio, Telegram API и т.д.)
    Ответственность: Только низкоуровневое взаимодействие с API внешних сервисов
    """

    @abstractmethod
    async def send_message(self, to: str, message: str) -> Optional[str]:
        """
        Отправляет сообщение получателю через внешний API

        Args:
            to: Идентификатор получателя (телефон, chat_id и т.д.)
            message: Текст сообщения

        Returns:
            Optional[str]: ID отправленного сообщения или None в случае ошибки
        """
        pass

    @abstractmethod
    async def send_template_message(self, to: str, template_name: str, lang: Optional[str] = None,
                                    params: Dict[str, Any] = None) -> Optional[str]:
        """
        Отправляет шаблонное сообщение через внешний API

        Args:
            to: Идентификатор получателя
            template_name: Ключ шаблона сообщения
            lang: Код языка (если None, будет определен автоматически)
            params: Параметры для подстановки в шаблон

        Returns:
            Optional[str]: ID отправленного сообщения или None в случае ошибки
        """
        pass