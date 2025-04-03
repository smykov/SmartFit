from abc import ABC, abstractmethod
from typing import List


class IMessageService(ABC):
    """Интерфейс для сервиса отправки сообщений"""
    
    @abstractmethod
    async def send_message(self, to_phone: str, message: str, context: str = None) -> bool:
        """
        Отправляет текстовое сообщение
        
        Args:
            to_phone: Номер телефона получателя
            message: Текст сообщения
            context: Контекст сообщения (например, шаг онбординга)
            
        Returns:
            bool: Результат отправки
        """
        pass
    
    @abstractmethod
    async def send_messages(self, to_phone: str, messages: List[str]) -> bool:
        """
        Отправляет несколько текстовых сообщений последовательно
        
        Args:
            to_phone: Номер телефона получателя
            messages: Список текстовых сообщений
            
        Returns:
            bool: Результат отправки
        """
        pass
    
    @abstractmethod
    async def send_template_message(self, to_phone: str, template_name: str, params: List[str] = None) -> bool:
        """
        Отправляет шаблонное сообщение
        
        Args:
            to_phone: Номер телефона получателя
            template_name: Название шаблона
            params: Параметры для шаблона
            
        Returns:
            bool: Результат отправки
        """
        pass
    
    @abstractmethod
    async def can_send_reminder(self, phone_number: str, reminder_type: str, min_interval_seconds: int) -> bool:
        """
        Проверяет, можно ли отправить напоминание определенного типа
        
        Args:
            phone_number: Номер телефона пользователя
            reminder_type: Тип напоминания
            min_interval_seconds: Минимальный интервал между напоминаниями в секундах
            
        Returns:
            bool: True, если можно отправить напоминание
        """
        pass
    
    @abstractmethod
    async def record_reminder_sent(self, phone_number: str, reminder_type: str) -> None:
        """
        Записывает информацию об отправленном напоминании
        
        Args:
            phone_number: Номер телефона пользователя
            reminder_type: Тип напоминания
        """
        pass
