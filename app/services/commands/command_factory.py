import logging
from typing import Dict, Any, Optional

from pip._internal.commands.help import HelpCommand

from app.services.commands.commands.compliance_command import ComplianceCommand
from app.services.commands.commands.diet_command import DietCommand
from app.services.commands.commands.shopping_list_command import ShoppingListCommand
from app.services.commands.commands.stats_command import StatsCommand
from app.services.commands.commands.water_command import WaterCommand
from app.services.commands.commands.weight_command import WeightCommand
from app.services.commands.interfaces.command_interface import ICommand


class CommandFactory:
    """
    Фабрика для создания команд с внедрением зависимостей
    """

    def __init__(self, dependencies: Dict[str, Any]):
        """
        Инициализация фабрики с зависимостями
        
        Args:
            dependencies: Словарь зависимостей для создания команд
        """
        self.dependencies = dependencies
        self.logger = logging.getLogger(self.__class__.__name__)

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

    def create_command(self, command_type: str, user: Dict[str, Any]) -> Optional[ICommand]:
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
            command_dependencies['user'] = user

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
