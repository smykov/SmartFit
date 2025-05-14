# app/services/llm/base_llm_service.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class LLMServiceError(Exception):
    """Базовый класс для исключений, связанных с LLM-сервисами"""

    def __init__(self, message: str, raw_response: Any = None, error_type: str = "general"):
        super().__init__(message)
        self.message = message
        self.raw_response = raw_response
        self.error_type = error_type  # Тип ошибки: timeout, parse_error, server_error и т.д.


class LLMTimeoutError(LLMServiceError):
    """Исключение для ошибок таймаута при запросе к LLM-сервису"""

    def __init__(self, message: str, raw_response: Any = None):
        super().__init__(message, raw_response, "timeout")


class LLMParseError(LLMServiceError):
    """Исключение для ошибок парсинга ответа от LLM-сервиса"""

    def __init__(self, message: str, raw_response: Any = None):
        super().__init__(message, raw_response, "parse_error")


class LLMServerError(LLMServiceError):
    """Исключение для серверных ошибок LLM-сервиса"""

    def __init__(self, message: str, status_code: int = 0, raw_response: Any = None):
        super().__init__(message, raw_response, "server_error")
        self.status_code = status_code


class BaseLLMService(ABC):
    """
    Абстрактный базовый класс для сервисов языковых моделей (LLM).
    Определяет общий интерфейс для всех LLM-сервисов.
    """

    @abstractmethod
    async def generate_completion(self,
                                  system_prompt: str,
                                  user_prompt: str,
                                  history_messages: Optional[List[Dict[str, str]]] = None,
                                  temperature: float = 0.7,
                                  max_tokens: int = 2000) -> str:
        """
        Генерирует ответ на основе системного и пользовательского промптов.

        Args:
            system_prompt: Системный промпт, задающий контекст и роль модели
            user_prompt: Пользовательский промпт (запрос)
            history_messages: Предыдущие промпты
            temperature: Температура (степень случайности) генерации
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            str: Сгенерированный текст

        Raises:
            LLMTimeoutError: При превышении времени ожидания ответа
            LLMParseError: При ошибке парсинга ответа
            LLMServerError: При серверной ошибке LLM-сервиса
            LLMServiceError: При прочих ошибках
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
