import logging

from app.services.llm.base_llm_service import BaseLLMService
from app.services.llm.deepseek_llm_service import DeepSeekLLMService
from app.services.llm.hybrid_llm_service import HybridLLMService
from app.services.llm.openai_llm_service import OpenAILLMService
from config import settings

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    Фабрика для создания экземпляров LLM-сервисов
    """

    @staticmethod
    def create_llm_service(provider: str = None) -> BaseLLMService:
        """
        Создает экземпляр LLM-сервиса на основе указанного провайдера

        Args:
            provider: Провайдер LLM ('openai', 'deepseek', 'hybrid' или None для значения из конфигурации)

        Returns:
            BaseLLMService: Экземпляр LLM-сервиса
        """
        # Если провайдер не указан, берем из настроек
        if provider is None:
            provider = settings.LLM_PROVIDER

        provider = provider.lower()

        if provider == "openai":
            logger.info("Creating OpenAI LLM service")
            return OpenAILLMService(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL
            )

        elif provider == "deepseek":
            logger.info("Creating DeepSeek LLM service")
            return DeepSeekLLMService(
                api_key=settings.DEEPSEEK_API_KEY,
                model=settings.DEEPSEEK_MODEL,
                api_base=settings.DEEPSEEK_API_BASE
            )

        elif provider == "hybrid":
            logger.info("Creating Hybrid LLM service")

            # Создаем сервисы для гибридного подхода
            openai_service = OpenAILLMService(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL
            )

            deepseek_service = DeepSeekLLMService(
                api_key=settings.DEEPSEEK_API_KEY,
                model=settings.DEEPSEEK_MODEL,
                api_base=settings.DEEPSEEK_API_BASE
            )

            # Карта задач для разных сервисов
            services_map = {
                "default": openai_service,  # По умолчанию используем OpenAI
                "diet_plan": openai_service,  # Для сложных задач - OpenAI
                "nutrition_question": deepseek_service,  # Для простых ответов - DeepSeek
                "shopping_list": deepseek_service  # Для списка покупок - DeepSeek
            }

            # Используем определенные в конфигурации сервисы для каждой задачи
            if hasattr(settings, 'LLM_TASK_MAPPING') and settings.LLM_TASK_MAPPING:
                for task, task_provider in settings.LLM_TASK_MAPPING.items():
                    if task_provider.lower() == 'openai':
                        services_map[task] = openai_service
                    elif task_provider.lower() == 'deepseek':
                        services_map[task] = deepseek_service

            return HybridLLMService(
                services_map=services_map,
                default_service_key="default"
            )

        else:
            logger.warning(f"Unknown LLM provider: {provider}, falling back to OpenAI")
            return OpenAILLMService(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL
            )

    @staticmethod
    def get_default_llm_service() -> BaseLLMService:
        """
        Возвращает LLM-сервис по умолчанию из настроек

        Returns:
            BaseLLMService: Экземпляр LLM-сервиса
        """
        return LLMFactory.create_llm_service()


# Создаем глобальный экземпляр LLM-сервиса для использования в приложении
llm_service = LLMFactory.get_default_llm_service()