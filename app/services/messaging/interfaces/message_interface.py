# app/services/messaging/interfaces/message_interface.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IMessengerService(ABC):
    """
    Интерфейс для сервиса отправки сообщений
    Ответственность: Высокоуровневая бизнес-логика отправки сообщений
    """

    @abstractmethod
    async def send_message(self, recipient_id: str, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Отправляет текстовое сообщение

        Args:
            recipient_id: Идентификатор получателя
            message: Текст сообщения
            context: Контекст сообщения (шаг онбординга, тип мессенджера и т.д.)

        Returns:
            bool: Результат отправки
        """
        pass

    @abstractmethod
    async def send_messages(self, recipient_id: str, messages: List[str], context: Dict[str, Any] = None) -> bool:
        """
        Отправляет несколько текстовых сообщений последовательно

        Args:
            recipient_id: Идентификатор получателя
            messages: Список текстовых сообщений
            context: Контекст сообщений

        Returns:
            bool: Результат отправки
        """
        pass

    @abstractmethod
    async def send_template_message(self, recipient_id: str, template_name: str, user_id: Optional[str] = None,
                                    params: Dict[str, Any] = None) -> bool:
        """
        Отправляет шаблонное сообщение

        Args:
            recipient_id: Идентификатор получателя
            template_name: Название шаблона
            user_id: ID пользователя для определения языка (если None, используется язык по умолчанию)
            params: Параметры для шаблона

        Returns:
            bool: Результат отправки
        """
        pass

    @abstractmethod
    async def can_send_reminder(self, recipient_id: str, reminder_type: str, min_interval_seconds: int) -> bool:
        """
        Проверяет, можно ли отправить напоминание определенного типа

        Args:
            recipient_id: Идентификатор получателя
            reminder_type: Тип напоминания
            min_interval_seconds: Минимальный интервал между напоминаниями в секундах

        Returns:
            bool: True, если можно отправить напоминание
        """
        pass

    @abstractmethod
    async def record_reminder_sent(self, recipient_id: str, reminder_type: str) -> None:
        """
        Записывает информацию об отправленном напоминании

        Args:
            recipient_id: Идентификатор получателя
            reminder_type: Тип напоминания
        """
        pass