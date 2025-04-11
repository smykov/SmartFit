import logging
from typing import Dict, Any, Optional

from app.services.diet.diet_service_interface import IDietService
from app.services.tracking.tracking_service_interface import ITrackingService
from app.services.messaging.message_interface import IMessageService
from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.localization.localization_interface import ILocalizationService

from app.services.commands.command_factory import CommandFactory
from app.localization.command_handler_messages import CommandHandlerMessages


class CommandHandlerService:
    """
    Сервис для обработки команд пользователя
    """

    def __init__(
            self,
            user_repository: IUserRepository,
            message_service: IMessageService,
            tracking_service: Optional[ITrackingService] = None,
            diet_service: Optional[IDietService] = None,
            localization_service: Optional[ILocalizationService] = None
    ):
        """
        Инициализация сервиса обработки команд

        Args:
            user_repository: Репозиторий пользователей
            message_service: Сервис отправки сообщений
            tracking_service: Сервис трекинга (опционально)
            diet_service: Сервис диет (опционально)
            localization_service: Сервис локализации (опционально)
        """
        self.user_repository = user_repository
        self.message_service = message_service
        self.tracking_service = tracking_service
        self.diet_service = diet_service
        self.localization_service = localization_service
        self.messages = CommandHandlerMessages()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Создаем фабрику команд с типизированными зависимостями
        self.command_factory = CommandFactory(
            user_repository=user_repository,
            message_service=message_service,
            tracking_service=tracking_service,
            diet_service=diet_service,
            localization_service=localization_service
        )

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
                    "error": "User not found"
                }

            # Создаем команду через фабрику
            command = self.command_factory.create_command(command_type)

            # Если команда не найдена
            if not command:
                language = await self.localization_service.get_user_language(
                    user['id']) if self.localization_service else None
                return {
                    "success": False,
                    "message": self.messages.COMMAND_NOT_FOUND
                }

            # Проверяем предварительные условия выполнения команды
            if not await command.can_execute(user['id']):
                return {
                    "success": False,
                    "message": command.get_error_message()
                }

            # Выполняем команду
            result = await command.execute(user['id'], command_params)

            return result

        except Exception as e:
            # Логируем неожиданные ошибки
            self.logger.error(f"Ошибка при обработке команды: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": str(e)
            }

    def get_help_message(self, lang: Optional[str] = None) -> str:
        """
        Получение справочного сообщения со списком команд

        Args:
            lang: Код языка (опционально)

        Returns:
            str: Справочное сообщение
        """
        return self.messages.get_help_message(lang)
