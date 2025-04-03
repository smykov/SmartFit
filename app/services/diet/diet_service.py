# app/services/diet/diet_service.py

from typing import Dict, Any, List, Optional, Tuple
from datetime import date

from app.localization.messages import DietMessages
from app.services.diet.base_service import BaseDietService
from app.services.diet.diet_plan_manager import DietPlanManager
from app.services.diet.shopping_list_manager import ShoppingListManager
from app.services.diet.diet_formatter import DietFormatter
from app.services.llm import llm_service


class DietService(BaseDietService):
    """Основной сервис для работы с диетами, использующий специализированные компоненты"""

    def __init__(self):
        """Инициализация сервиса диет с необходимыми компонентами"""
        super().__init__()
        self.diet_plan_manager = DietPlanManager(llm_service)
        self.shopping_list_manager = ShoppingListManager(llm_service)
        self.formatter = DietFormatter()
        self.messages = DietMessages()

    # Методы для делегирования вызовов соответствующим компонентам

    # Методы делегирования для DietPlanManager
    async def generate_short_diet_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Генерирует краткую версию плана диеты

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Краткий план диеты
        """
        return await self.diet_plan_manager.generate_short_diet_plan(user_id)

    async def approve_short_diet_plan(self, plan_id: str) -> bool:
        """
        Отмечает краткий план диеты как согласованный

        Args:
            plan_id: ID плана диеты

        Returns:
            bool: Результат операции
        """
        return await self.diet_plan_manager.approve_short_diet_plan(plan_id)

    async def update_short_diet_plan(self, plan_id: str, updated_days: Dict[str, Any], comment: str = None) -> Tuple[
        bool, Dict[str, Any]]:
        """
        Обновляет краткую версию плана питания

        Args:
            plan_id: ID плана диеты
            updated_days: Словарь {день_недели: данные_на_день}
            comment: Комментарий по изменению

        Returns:
            Tuple[bool, Dict[str, Any]]: (успех, обновленный план)
        """
        return await self.diet_plan_manager.update_short_diet_plan(plan_id, updated_days, comment)

    async def update_diet_plan_partially(self, diet_plan_id: str, updated_days: Dict[str, Any], comment: str = None) -> \
    Tuple[bool, Dict[str, Any]]:
        """
        Обновляет частично план питания

        Args:
            diet_plan_id: ID плана диеты
            updated_days: Словарь {дата: данные на день}
            comment: Комментарий по изменению

        Returns:
            Tuple[bool, Dict[str, Any]]: (успех, обновленный план)
        """
        return await self.diet_plan_manager.update_diet_plan_partially(diet_plan_id, updated_days, comment)

    async def get_current_diet(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает текущий активный план диеты пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Текущий план диеты
        """
        return await self.diet_plan_manager.get_current_diet(user_id)

    async def get_diet_for_day(self, user_id: str, day_date: date) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты на конкретный день

        Args:
            user_id: ID пользователя
            day_date: Дата, на которую нужен план

        Returns:
            Optional[Dict[str, Any]]: План на день
        """
        return await self.diet_plan_manager.get_diet_for_day(user_id, day_date)

    async def get_today_diet(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты на сегодняшний день

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: План на сегодня
        """
        return await self.diet_plan_manager.get_today_diet(user_id)

    async def get_diet_for_weekday(self, user_id: str, weekday: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты на конкретный день недели

        Args:
            user_id: ID пользователя
            weekday: День недели ('monday', 'tuesday', и т.д.)

        Returns:
            Optional[Dict[str, Any]]: План на день
        """
        return await self.diet_plan_manager.get_diet_for_weekday(user_id, weekday)

    async def update_diet_plan(self, diet_plan_id: str, update_request: str) -> Dict[str, Any]:
        """
        Обновляет план диеты на основе запроса пользователя

        Args:
            diet_plan_id: ID плана диеты
            update_request: Текст запроса пользователя на изменение

        Returns:
            Dict[str, Any]: Результат обновления
        """
        return await self.diet_plan_manager.update_diet_plan(diet_plan_id, update_request)

    async def update_short_diet_plan_by_request(self, plan_id: str, update_request: str) -> Dict[str, Any]:
        """
        Обновляет краткий план диеты на основе запроса пользователя

        Args:
            plan_id: ID плана диеты
            update_request: Текст запроса пользователя на изменение

        Returns:
            Dict[str, Any]: Результат обновления
        """
        return await self.diet_plan_manager.update_short_diet_plan_by_request(plan_id, update_request)

    # Методы делегирования для ShoppingListManager
    async def generate_shopping_list(self, diet_plan_id: str) -> Dict[str, Any]:
        """
        Создает список покупок на основе плана диеты

        Args:
            diet_plan_id: ID плана диеты

        Returns:
            Dict[str, Any]: Список покупок
        """
        return await self.shopping_list_manager.generate_shopping_list(diet_plan_id)

    async def mark_product_as_purchased(self, user_id: str, product_name: str) -> Dict[str, Any]:
        """
        Отмечает продукт как купленный в списке покупок

        Args:
            user_id: ID пользователя
            product_name: Название продукта

        Returns:
            Dict[str, Any]: Результат операции
        """
        return await self.shopping_list_manager.mark_product_as_purchased(user_id, product_name)

    # Методы делегирования для DietFormatter
    def get_diet_summary(self, diet_plan: Dict[str, Any]) -> Tuple[str, str]:
        """
        Создает сводку плана диеты и сообщение с командами

        Args:
            diet_plan: План диеты

        Returns:
            Tuple[str, str]: (сводка плана, команды для взаимодействия)
        """
        return self.formatter.get_diet_summary(diet_plan)

    def get_short_diet_summary(self, diet_plan: Dict[str, Any]) -> str:
        """
        Создает сводку краткой версии плана диеты

        Args:
            diet_plan: План диеты

        Returns:
            str: Отформатированная сводка плана
        """
        return self.formatter.get_short_diet_summary(diet_plan)

    def get_full_diet_plan(self, diet_plan: Dict[str, Any]) -> List[str]:
        """
        Создает полный план диеты на все дни

        Args:
            diet_plan: План диеты

        Returns:
            List[str]: Список сообщений с планом диеты
        """
        return self.formatter.get_full_diet_plan(diet_plan)

    def get_day_diet_plan(self, diet_plan: Dict[str, Any], day_date: date = None) -> str:
        """
        Создает детальный план диеты на конкретный день

        Args:
            diet_plan: План диеты
            day_date: Дата, на которую нужен план

        Returns:
            str: Сообщение с планом на день
        """
        return self.formatter.get_day_diet_plan(diet_plan, day_date)

    def format_shopping_list(self, shopping_list_data: Dict[str, Any]) -> str:
        """
        Форматирует список покупок для отправки пользователю

        Args:
            shopping_list_data: Данные списка покупок

        Returns:
            str: Отформатированный список покупок
        """
        return self.formatter.format_shopping_list(shopping_list_data)