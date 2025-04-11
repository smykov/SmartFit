import logging
from typing import Dict, Any, Optional

from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.commands.commands.compliance_command import ComplianceCommand
from app.services.commands.commands.diet_command import DietCommand
from app.services.commands.commands.help_command import HelpCommand
from app.services.commands.commands.shopping_list_command import ShoppingListCommand
from app.services.commands.commands.stats_command import StatsCommand
from app.services.commands.commands.water_command import WaterCommand
from app.services.commands.commands.weight_command import WeightCommand
from app.services.commands.interfaces.command_interface import ICommand
from app.services.diet.diet_service_interface import IDietService
from app.services.llm import BaseLLMService
from app.services.localization.localization_interface import ILocalizationService
from app.services.messaging.message_interface import IMessageService
from app.services.tracking.tracking_service_interface import ITrackingService


class CommandFactory:
    """
    Фабрика для создания команд с внедрением зависимостей
    """

    def __init__(self, user_repository: IUserRepository,
                 message_service: IMessageService,
                 tracking_service: ITrackingService = None,
                 diet_service: IDietService = None,
                 localization_service: ILocalizationService = None,
                 llm_service: BaseLLMService = None):
        """
        Инициализация фабрики с зависимостями

        Args:
            user_repository: Репозиторий для работы с пользователями
            message_service: Сервис для отправки сообщений
            tracking_service: Сервис трекинга (опционально)
            diet_service: Сервис диет (опционально)
            localization_service: Сервис локализации (опционально)
            llm_service: Сервис языковой модели (опционально)
        """
        self.user_repository = user_repository
        self.message_service = message_service
        self.tracking_service = tracking_service
        self.diet_service = diet_service
        self.localization_service = localization_service
        self.llm_service = llm_service
        self.logger = logging.getLogger(self.__class__.__name__)

        # Создаем словарь зависимостей для обратной совместимости
        self.dependencies = {
            "user_repository": user_repository,
            "message_service": message_service,
            "tracking_service": tracking_service,
            "diet_service": diet_service,
            "localization_service": localization_service,
            "llm_service": llm_service
        }

        # Маппинг типов команд к классам команд
        self.command_map = {
            "weight": WeightCommand,
            "water": WaterCommand,
            "help": HelpCommand,
            "diet": DietCommand,
            # "diet_today": DietTodayCommand,
            # "diet_tomorrow": DietTomorrowCommand,
            # "diet_full": DietFullCommand,
            "shopping_list": ShoppingListCommand,
            # "product_bought": ProductBoughtCommand,
            "stats": StatsCommand,
            "meal_compliance": ComplianceCommand,
            # "diet_update": DietUpdateCommand,
        }

    def create_command(self, command_type: str) -> Optional[ICommand]:
        """
        Создает экземпляр команды по ее типу

        Args:
            command_type: Тип команды
            user: Данные пользователя

        Returns:
            Optional[ICommand]: Экземпляр команды или None
        """
        try:
            # Добавляем данные пользователя в зависимости
            command_dependencies = self.dependencies.copy()

            # Находим класс команды по типу
            command_class = self.command_map.get(command_type)

            if command_class:
                self.logger.info(f"Создание команды типа: {command_type}")
                return command_class(command_dependencies)
            else:
                self.logger.warning(f"Класс команды не найден для типа: {command_type}")
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при создании команды типа {command_type}: {str(e)}", exc_info=True)
            return None
