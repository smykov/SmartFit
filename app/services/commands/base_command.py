import logging
from typing import Dict, Any, Optional

from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.commands.interfaces.command_interface import ICommand
from app.services.diet.diet_service_interface import IDietService
from app.services.tracking.tracking_service_interface import ITrackingService
from app.services.messaging.message_interface import IMessageService
from app.services.localization.localization_interface import ILocalizationService


class BaseCommand(ICommand):
    """
    Базовый класс для всех команд
    """

    def __init__(self, dependencies: Dict[str, Any]):
        """
        Инициализация базовой команды с зависимостями

        Args:
            dependencies: Словарь зависимостей для команды
        """
        self.dependencies = dependencies
        self.logger = logging.getLogger(self.__class__.__name__)

        # Для удобства доступа, извлекаем общие зависимости с явной типизацией
        if 'user_repository' in dependencies:
            self.user_repository: IUserRepository = dependencies['user_repository']
        if 'message_service' in dependencies:
            self.message_service: IMessageService = dependencies['message_service']
        if 'tracking_service' in dependencies:
            self.tracking_service: ITrackingService = dependencies['tracking_service']
        if 'diet_service' in dependencies:
            self.diet_service: IDietService = dependencies['diet_service']
        if 'localization_service' in dependencies:
            self.localization_service: ILocalizationService = dependencies['localization_service']

    def get_localized_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        """
        Получает локализованное сообщение

        Args:
            key: Ключ сообщения
            lang: Код языка
            **params: Параметры для форматирования

        Returns:
            str: Локализованное сообщение
        """
        if hasattr(self, 'localization_service') and self.localization_service:
            return self.localization_service.get_message(key, lang, **params)
        return key  # Если сервис локализации недоступен, возвращаем ключ

    async def can_execute(self, user_id: str) -> bool:
        """
        Базовая проверка возможности выполнения команды
        По умолчанию всегда возвращает True

        Args:
            user_id: ID пользователя

        Returns:
            bool: Возможность выполнения команды
        """
        return True

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Базовый метод выполнения команды

        Args:
            user_id: ID пользователя
            params: Дополнительные параметры команды

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        raise NotImplementedError("Метод execute должен быть реализован в дочернем классе")

    def get_error_message(self) -> str:
        """
        Базовое сообщение об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message("commands.errors.command_not_found")