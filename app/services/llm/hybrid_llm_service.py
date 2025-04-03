import json
import logging
from typing import Dict, Any, List, Optional

from app.services.llm.base_llm_service import BaseLLMService
from app.templates.formatting_helpers import clean_json_from_markdown
from app.templates.prompts import create_diet_system_prompt, update_diet_user_prompt

logger = logging.getLogger(__name__)


class HybridLLMService(BaseLLMService):
    """
    Гибридный сервис, который использует разные LLM для разных задач

    Это позволяет, например, использовать более мощную и дорогую модель
    для сложных задач и более дешевую для простых.
    """

    def __init__(self, services_map: Dict[str, BaseLLMService], default_service_key: str):
        """
        Инициализация гибридного сервиса

        Args:
            services_map: Словарь с сервисами LLM, где ключ - название задачи
            default_service_key: Ключ сервиса по умолчанию
        """
        self.services = services_map
        self.default_service_key = default_service_key

        if self.default_service_key not in self.services:
            raise ValueError(f"Default service key '{default_service_key}' not found in services map")

        logger.info(f"Initialized Hybrid LLM service with {len(services_map)} services, default: {default_service_key}")

    def get_service_for_task(self, task: str) -> BaseLLMService:
        """
        Возвращает сервис для указанной задачи

        Args:
            task: Название задачи

        Returns:
            BaseLLMService: Сервис для задачи
        """
        return self.services.get(task, self.services[self.default_service_key])

    async def generate_completion(self,
                                  system_prompt: str,
                                  user_prompt: str,
                                  history_messages: Optional[List[Dict[str, str]]] = None,
                                  temperature: float = 0.7,
                                  max_tokens: int = 2000,
                                  task: str = "default") -> str:
        """
        Генерирует ответ, используя соответствующий LLM для задачи

        Args:
            system_prompt: Системный промпт
            user_prompt: Пользовательский промпт
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            task: Название задачи для выбора LLM

        Returns:
            str: Сгенерированный текст
        """
        service = self.get_service_for_task(task)
        return await service.generate_completion(system_prompt, user_prompt, temperature, max_tokens)

    async def generate_diet_plan(self,
                                 user_data: Dict[str, Any],
                                 days: int = 7,
                                 product_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Генерирует план диеты, используя соответствующий LLM

        Args:
            user_data: Данные пользователя
            days: Количество дней для плана
            product_list: Список доступных продуктов

        Returns:
            Dict[str, Any]: План диеты
        """
        service = self.get_service_for_task("diet_plan")
        return await service.generate_diet_plan(user_data, days, product_list)

    async def answer_nutrition_question(self,
                                        user_id: str,
                                        question: str) -> str:
        """
        Отвечает на вопрос о питании, используя соответствующий LLM

        Args:
            user_id: ID пользователя
            question: Вопрос о питании

        Returns:
            str: Ответ на вопрос
        """
        service = self.get_service_for_task("nutrition_question")
        return await service.answer_nutrition_question(user_id, question)

    async def create_shopping_list(self,
                                   diet_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Создает список покупок, используя соответствующий LLM

        Args:
            diet_plan: План диеты

        Returns:
            List[Dict[str, Any]]: Список покупок
        """
        service = self.get_service_for_task("shopping_list")
        return await service.create_shopping_list(diet_plan)

    async def update_diet_plan(self,
                               diet_plan: Dict[str, Any],
                               update_request: str) -> Dict[str, Any]:
        """
        Обновляет план диеты на основе запроса пользователя с использованием DeepSeek

        Args:
            diet_plan: Существующий план диеты
            update_request: Запрос пользователя на изменение плана

        Returns:
            Dict[str, Any]: Обновленные дни плана и комментарий
        """
        try:
            system_prompt = create_diet_system_prompt()
            user_prompt = update_diet_user_prompt(update_request)

            history_messages = []

            # Проверяем наличие метаданных генерации
            if "diet_generation_metadata" in diet_plan and all(key in diet_plan["diet_generation_metadata"]
                                                               for key in ["system_prompt", "user_prompt", "response"]):
                metadata = diet_plan["diet_generation_metadata"]
                history_messages = [
                    {"role": "system", "content": metadata["system_prompt"]},
                    {"role": "user", "content": metadata["user_prompt"]},
                    {"role": "assistant", "content": metadata["response"]},
                    # {"role": "assistant", "content": json.dumps(diet_plan)},
                ]

            response = await self.generate_completion(system_prompt, user_prompt, history_messages)

            # Очищаем ответ от маркдауна, если есть
            response = clean_json_from_markdown(response)

            # Парсим JSON-ответ
            try:
                updates = json.loads(response)

                # Проверяем корректность формата ответа
                if "updated_days" not in updates:
                    logger.error(f"Некорректный формат ответа от ИИ: {response}")
                    return {"error": "Некорректный формат ответа"}

                return updates
            except json.JSONDecodeError:
                logger.error(f"Не удалось распарсить ответ ИИ как JSON: {response}")
                return {"error": "Ошибка при обработке ответа", "raw_response": response}

        except Exception as e:
            logger.error(f"Ошибка при обновлении плана диеты: {str(e)}")
            return {"error": str(e)}