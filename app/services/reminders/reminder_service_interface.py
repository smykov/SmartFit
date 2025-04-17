# app/services/reminders/reminder_service_interface.py
from abc import ABC, abstractmethod


class IReminderService(ABC):
    """
    Интерфейс для сервиса напоминаний
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Инициализация сервиса и запуск регулярных задач"""
        pass

    @abstractmethod
    async def send_onboarding_reminders(self) -> None:
        """Отправляет напоминания пользователям с незавершенным онбордингом"""
        pass

    @abstractmethod
    async def send_plan_approval_reminders(self) -> None:
        """Отправляет напоминания о необходимости согласования плана питания"""
        pass

    @abstractmethod
    async def send_tracking_reminders(self) -> None:
        """Отправляет напоминания о трекинге с учетом времени суток"""
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