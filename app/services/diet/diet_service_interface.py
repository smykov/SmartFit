from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import date


class IDietService(ABC):
    """
    Интерфейс сервиса для работы с диетами
    """

    @abstractmethod
    async def generate_short_diet_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Генерирует краткую версию плана диеты для согласования

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Краткий план диеты или None
        """
        pass

    @abstractmethod
    async def generate_full_diet_plan(self, short_plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Генерирует полную версию плана диеты

        Args:
            short_plan_id: ID краткого плана диеты

        Returns:
            Optional[Dict[str, Any]]: Полный план диеты или None
        """
        pass

    @abstractmethod
    async def approve_short_diet_plan(self, plan_id: str) -> bool:
        """
        Отмечает краткий план диеты как согласованный

        Args:
            plan_id: ID плана диеты

        Returns:
            bool: Результат операции
        """
        pass

    @abstractmethod
    async def start_full_diet_generation(self, user_id: str, short_plan_id: str) -> bool:
        """
        Запускает фоновую генерацию полного плана диеты

        Args:
            user_id: ID пользователя
            short_plan_id: ID краткой версии плана диеты

        Returns:
            bool: Успешность запуска генерации
        """
        pass

    @abstractmethod
    async def get_current_diet(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает текущий активный план диеты пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Текущий план диеты или None
        """
        pass

    @abstractmethod
    async def get_diet_for_day(self, user_id: str, day_date: date) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты на конкретный день

        Args:
            user_id: ID пользователя
            day_date: Дата, на которую нужен план

        Returns:
            Optional[Dict[str, Any]]: План на день или None
        """
        pass

    @abstractmethod
    async def update_diet_plan(self, diet_plan_id: str, update_request: str) -> Dict[str, Any]:
        """
        Обновляет план диеты на основе запроса пользователя

        Args:
            diet_plan_id: ID плана диеты
            update_request: Текст запроса пользователя на изменение

        Returns:
            Dict[str, Any]: Результат обновления
        """
        pass

    @abstractmethod
    async def generate_shopping_list(self, diet_plan_id: str) -> Dict[str, Any]:
        """
        Создает список покупок на основе плана диеты

        Args:
            diet_plan_id: ID плана диеты

        Returns:
            Dict[str, Any]: Список покупок
        """
        pass

    @abstractmethod
    async def mark_product_as_purchased(self, user_id: str, product_name: str) -> Dict[str, Any]:
        """
        Отмечает продукт как купленный в списке покупок

        Args:
            user_id: ID пользователя
            product_name: Название продукта

        Returns:
            Dict[str, Any]: Результат операции
        """
        pass

    @abstractmethod
    async def answer_nutrition_question(self, user_id: str, question: str) -> str:
        """
        Отвечает на вопрос пользователя о питании

        Args:
            user_id: ID пользователя
            question: Вопрос о питании

        Returns:
            str: Ответ на вопрос
        """
        pass

    @abstractmethod
    def get_diet_summary(self, diet_plan: Dict[str, Any], lang: str) -> str:
        """
        Создает сводку плана диеты

        Args:
            diet_plan: План диеты
            lang: Код языка (по умолчанию используется системный язык)

        Returns:
            str: Сводка плана диеты
        """
        pass

    @abstractmethod
    def get_full_diet_plan(self, diet_plan: Dict[str, Any]) -> List[str]:
        """
        Создает полный план диеты на все дни

        Args:
            diet_plan: План диеты

        Returns:
            List[str]: Список сообщений с планом диеты
        """
        pass

    @abstractmethod
    def format_shopping_list(self, shopping_list_data: Dict[str, Any]) -> str:
        """
        Форматирует список покупок для отправки пользователю

        Args:
            shopping_list_data: Данные списка покупок

        Returns:
            str: Отформатированный список покупок
        """
        pass

    @abstractmethod
    async def get_pending_diet_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты, ожидающий согласования пользователем

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: План диеты или None, если такого плана нет
        """
        pass

    @abstractmethod
    async def get_pending_plans(self) -> List[Dict[str, Any]]:
        """
        Получает все планы диет со статусом "pending"

        Returns:
            List[Dict[str, Any]]: Список планов диет в ожидании одобрения
        """
        pass

    @abstractmethod
    async def update_short_diet_plan_by_request(self, plan_id: str, update_request: str) -> Dict[str, Any]:
        """
        Обновляет краткий план диеты на основе запроса пользователя

        Args:
            plan_id: ID плана диеты
            update_request: Текст запроса пользователя на изменение

        Returns:
            Dict[str, Any]: Результат обновления
        """
        pass

    @abstractmethod
    def get_day_diet_plan(self, diet_plan: Dict[str, Any], day_date: date = None,
                          lang: Optional[str] = None) -> List[str]:
        """
        Создает детальный план диеты на конкретный день

        Args:
            diet_plan: План диеты
            day_date: Дата, на которую нужен план
            lang: Код языка

        Returns:
            List[str]: Сообщения с планом на день
        """
        pass
