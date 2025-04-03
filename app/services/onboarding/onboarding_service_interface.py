from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IOnboardingService(ABC):
    """
    Интерфейс сервиса онбординга
    Следует принципам:
    - Единственной ответственности (SRP)
    - Открытости/Закрытости (OCP)
    - Инверсии зависимостей (DIP)
    """

    @abstractmethod
    async def start_registration(self, phone_number: str) -> Dict[str, Any]:
        """
        Начинает процесс регистрации нового пользователя

        Args:
            phone_number: Номер телефона пользователя

        Returns:
            Dict[str, Any]: Результат начала регистрации
        """
        pass

    @abstractmethod
    async def continue_onboarding(self, user: Dict[str, Any], message_text: str) -> Dict[str, Any]:
        """
        Продолжает процесс онбординга для пользователя

        Args:
            user: Данные пользователя
            message_text: Текст сообщения от пользователя

        Returns:
            Dict[str, Any]: Результат продолжения онбординга
        """
        pass

    @abstractmethod
    async def complete_onboarding(self, user_id: str) -> Dict[str, Any]:
        """
        Завершает процесс онбординга

        Args:
            user_id: Идентификатор пользователя

        Returns:
            Dict[str, Any]: Результат завершения онбординга
        """
        pass

    @abstractmethod
    def validate_onboarding_step(self, step: str, message_text: str) -> Optional[Dict[str, Any]]:
        """
        Валидирует шаг онбординга

        Args:
            step: Текущий шаг онбординга
            message_text: Текст сообщения от пользователя

        Returns:
            Optional[Dict[str, Any]]: Обработанные данные или None
        """
        pass

    @abstractmethod
    async def get_next_onboarding_step(self, current_step: str) -> str:
        """
        Определяет следующий шаг онбординга

        Args:
            current_step: Текущий шаг онбординга

        Returns:
            str: Следующий шаг онбординга
        """
        pass

    @abstractmethod
    async def restore_onboarding_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Восстанавливает контекст онбординга для пользователя

        Args:
            user_id: Идентификатор пользователя

        Returns:
            Optional[Dict[str, Any]]: Контекст онбординга или None
        """
        pass