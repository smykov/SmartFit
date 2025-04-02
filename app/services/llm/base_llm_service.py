from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseLLMService(ABC):
    """
    Абстрактный базовый класс для сервисов языковых моделей (LLM).
    Определяет общий интерфейс для всех LLM-сервисов.
    """

    @abstractmethod
    async def generate_completion(self,
                                  system_prompt: str,
                                  user_prompt: str,
                                  temperature: float = 0.7,
                                  max_tokens: int = 2000) -> str:
        """
        Генерирует ответ на основе системного и пользовательского промптов.

        Args:
            system_prompt: Системный промпт, задающий контекст и роль модели
            user_prompt: Пользовательский промпт (запрос)
            temperature: Температура (степень случайности) генерации
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            str: Сгенерированный текст
        """
        pass

    @abstractmethod
    async def generate_diet_plan(self,
                                 user_data: Dict[str, Any],
                                 days: int = 7,
                                 product_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Генерирует план диеты на основе данных пользователя.

        Args:
            user_data: Данные пользователя (пол, возраст, вес, цели и т.д.)
            days: Количество дней для плана (по умолчанию 7)
            product_list: Список доступных продуктов с ценами

        Returns:
            Dict[str, Any]: План диеты
        """
        pass

    @abstractmethod
    async def update_short_diet_plan(self,
                                     diet_plan: Dict[str, Any],
                                     update_request: str) -> Dict[str, Any]:
        """
        Обновляет краткий план диеты на основе запроса пользователя

        Args:
            diet_plan: Текущий краткий план диеты
            update_request: Текст запроса пользователя на изменение

        Returns:
            Dict[str, Any]: Обновленные дни плана и комментарий
        """
        pass

    @abstractmethod
    async def update_diet_plan(self,
                               diet_plan: Dict[str, Any],
                               update_request: str) -> Dict[str, Any]:
        """
        Обновляет план диеты на основе запроса пользователя.

        Args:
            diet_plan: Текущий план диеты
            update_request: Текст запроса пользователя на изменение

        Returns:
            Dict[str, Any]: Обновленный фрагмент плана диеты
        """
        pass

    @abstractmethod
    async def answer_nutrition_question(self,
                                        user_id: str,
                                        question: str) -> str:
        """
        Отвечает на вопрос пользователя о питании.

        Args:
            user_id: ID пользователя
            question: Вопрос о питании

        Returns:
            str: Ответ на вопрос
        """
        pass

    @abstractmethod
    async def create_shopping_list(self,
                                   diet_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Создает список покупок на основе плана диеты.

        Args:
            diet_plan: План диеты

        Returns:
            List[Dict[str, Any]]: Список покупок
        """
        pass
