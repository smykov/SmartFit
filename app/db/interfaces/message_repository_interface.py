from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class IMessageRepository(ABC):
    """
    Интерфейс репозитория для работы с сообщениями
    Следует принципам:
    - Единственной ответственности (SRP)
    - Инверсии зависимостей (DIP)
    """

    @abstractmethod
    async def save_message(self, message_data: Dict[str, Any]) -> str:
        """
        Сохраняет сообщение в репозитории

        Args:
            message_data: Словарь с данными сообщения

        Returns:
            str: Идентификатор сохраненного сообщения
        """
        pass

    @abstractmethod
    async def save_sent_message(self, phone_number: str, message_id: str, message_text: str,
                                context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Сохраняет информацию об отправленном сообщении

        Args:
            phone_number: Номер телефона получателя
            message_id: ID сообщения от провайдера (например, Twilio)
            message_text: Текст сообщения
            context: Дополнительный контекст сообщения

        Returns:
            bool: Успешность операции
        """
        pass

    @abstractmethod
    async def update_pending_message_attempts(self, message_id: str) -> bool:
        """
        Обновляет счетчик попыток для неотправленного сообщения

        Args:
            message_id: ID сообщения

        Returns:
            bool: Успешность операции
        """

    pass

    @abstractmethod
    async def mark_pending_message_as_sent(self, message_id: str, provider_message_id: str) -> bool:
        """
        Помечает неотправленное сообщение как отправленное

        Args:
            message_id: ID сообщения в репозитории
            provider_message_id: ID сообщения от провайдера (например, Twilio)

        Returns:
            bool: Успешность операции
        """
        pass

    @abstractmethod
    async def save_pending_message(self, phone_number: str, message_text: str, error_type: str = "unknown",
                                   context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Сохраняет информацию о неотправленном сообщении для повторной попытки

        Args:
            phone_number: Номер телефона получателя
            message_text: Текст сообщения
            error_type: Тип ошибки при отправке
            context: Дополнительный контекст сообщения

        Returns:
            bool: Успешность операции
        """
        pass

    @abstractmethod
    async def find_pending_messages(self, max_age_hours: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Находит все неотправленные сообщения

        Args:
            max_age_hours: Максимальный возраст сообщений в часах

        Returns:
            List[Dict[str, Any]]: Список неотправленных сообщений
        """
        pass

    @abstractmethod
    async def mark_pending_message_as_expired(self, message_id: str) -> bool:
        """
        Помечает неотправленное сообщение как устаревшее

        Args:
            message_id: ID сообщения

        Returns:
            bool: Успешность операции
        """

    @abstractmethod
    async def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает сообщение по его идентификатору

        Args:
            message_id: Уникальный идентификатор сообщения

        Returns:
            Optional[Dict[str, Any]]: Данные сообщения или None
        """
        pass

    @abstractmethod
    async def find_messages_by_criteria(
            self,
            phone_number: Optional[str] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            message_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Находит сообщения по заданным критериям

        Args:
            phone_number: Номер телефона отправителя
            start_date: Начальная дата для поиска
            end_date: Конечная дата для поиска
            message_type: Тип сообщения

        Returns:
            List[Dict[str, Any]]: Список найденных сообщений
        """
        pass

    @abstractmethod
    async def is_processed(self, message_id: str) -> bool:
        """
        Проверяет, было ли сообщение обработано

        Args:
            message_id: Идентификатор сообщения

        Returns:
            bool: Статус обработки сообщения
        """
        pass

    @abstractmethod
    async def mark_as_processed(
            self,
            message_id: str,
            phone_number: str,
            message_text: str,
            timestamp: str
    ) -> None:
        """
        Помечает сообщение как обработанное

        Args:
            message_id: Идентификатор сообщения
            phone_number: Номер телефона отправителя
            message_text: Текст сообщения
            timestamp: Временная метка обработки
        """
        pass

    @abstractmethod
    async def count_messages_by_user(self, phone_number: str) -> int:
        """
        Подсчитывает количество сообщений от конкретного пользователя

        Args:
            phone_number: Номер телефона пользователя

        Returns:
            int: Количество сообщений
        """
        pass
