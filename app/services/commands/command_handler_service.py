import logging
from typing import Dict, Any, Optional

from app.services.diet.diet_service_interface import IDietService
from app.services.tracking.tracking_service_interface import ITrackingService
from app.services.messaging.interfaces.message_interface import IMessengerService
from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.localization.localization_interface import ILocalizationService
from app.constants.localization_keys import LocalizationKeys as LK

from app.services.commands.command_factory import CommandFactory
from app.services.commands.interfaces.command_handler_interface import ICommandHandler


class CommandHandlerService(ICommandHandler):
    """
    Сервис для обработки команд пользователя
    """

    def __init__(self, dependencies: Dict[str, Any]):
        """
        Инициализация сервиса обработки команд

        Args:
            dependencies: Словарь зависимостей для команды
        """
        super().__init__()

        self.dependencies = dependencies
        self.logger = logging.getLogger(self.__class__.__name__)

        # Для удобства доступа, извлекаем общие зависимости с явной типизацией
        if 'user_repository' in dependencies:
            self.user_repository: IUserRepository = dependencies['user_repository']
        if 'messenger_service' in dependencies:
            self.messenger_service: IMessengerService = dependencies['messenger_service']
        if 'tracking_service' in dependencies:
            self.tracking_service: ITrackingService = dependencies['tracking_service']
        if 'diet_service' in dependencies:
            self.diet_service: IDietService = dependencies['diet_service']
        if 'localization_service' in dependencies:
            self.localization_service: ILocalizationService = dependencies['localization_service']

        self.command_factory = CommandFactory(dependencies)

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

    async def handle_command(self, user: Dict[str, Any], command_type: str,
                             command_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Обработка команды пользователя

        Args:
            user: Данные пользователя
            command_type: Тип команды
            command_params: Параметры команды

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        try:
            # Проверяем, существует ли пользователь
            if not user or 'id' not in user:
                return {
                    "success": False,
                    "error": self.get_localized_message(LK.Messaging.USER_NOT_FOUND)
                }

            # Получаем язык пользователя
            lang = await self.localization_service.get_user_language(user['id']) if self.localization_service else None

            # Создаем команду через фабрику
            command = self.command_factory.create_command(command_type)

            # Если команда не найдена
            if not command:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.General.COMMAND_NOT_FOUND, lang)
                }

            # Проверяем предварительные условия выполнения команды
            if not await command.can_execute(user['id']):
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.General.PREREQUISITES_NOT_MET, lang)
                }

            # Выполняем команду
            result = await command.execute(user['id'], command_params)

            return result

        except Exception as e:
            # Логируем неожиданные ошибки
            self.logger.error(f"Ошибка при обработке команды: {str(e)}", exc_info=True)

            # Получаем язык пользователя
            lang = await self.localization_service.get_user_language(
                user['id']) if self.localization_service and 'id' in user else None

            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.General.EXECUTION_ERROR, lang)
            }

    def get_help_message(self, lang: Optional[str] = None) -> str:
        """
        Получение справочного сообщения со списком команд

        Args:
            lang: Код языка (опционально)

        Returns:
            str: Справочное сообщение
        """
        return self.get_localized_message(LK.Common.HELP_COMMANDS_LIST, lang)