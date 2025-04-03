from typing import Dict, Any, Optional
from app.services.commands.interfaces.command_interface import ICommand
from app.services.commands.commands.weight_command import WeightCommand
from app.services.commands.commands.water_command import WaterCommand
from app.services.commands.commands.diet_command import DietCommand
from app.services.commands.commands.shopping_list_command import ShoppingListCommand
from app.services.commands.commands.compliance_command import ComplianceCommand
from app.services.commands.commands.stats_command import StatsCommand

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
        
        # Маппинг типов команд к классам команд
        self.command_map = {
            "weight": WeightCommand,
            "water": WaterCommand,
            "diet": DietCommand,
            "shopping_list": ShoppingListCommand, 
            "meal_compliance": ComplianceCommand,
            "stats": StatsCommand
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
        # Добавляем данные пользователя в зависимости
        command_dependencies = self.dependencies.copy()
        command_dependencies['user'] = user

        # Находим класс команды по типу
        command_class = self.command_map.get(command_type)
        
        if command_class:
            return command_class(command_dependencies)
        
        return None