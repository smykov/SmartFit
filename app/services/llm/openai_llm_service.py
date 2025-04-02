import openai
import logging
from typing import Dict, Any, List, Optional
import json
import os

from app.services.llm.base_llm_service import BaseLLMService
from app.templates.formatting_helpers import clean_json_from_markdown
from app.templates.prompts import create_diet_system_prompt, create_diet_user_prompt, create_shopping_list_prompt, \
    create_nutrition_question_prompt, get_bot_commands_prompt, update_diet_user_prompt, create_short_diet_system_prompt, \
    update_short_diet_user_prompt

logger = logging.getLogger(__name__)


class OpenAILLMService(BaseLLMService):
    """Сервис для работы с OpenAI API"""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Инициализация сервиса OpenAI

        Args:
            api_key: Ключ API для OpenAI
            model: Модель для использования (по умолчанию gpt-3.5-turbo)
        """
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
        logger.info(f"Initialized OpenAI LLM service with model {model}")

    async def generate_completion(self,
                                  system_prompt: str,
                                  user_prompt: str,
                                  history_messages: Optional[List[Dict[str, str]]] = None,
                                  temperature: float = 0.7,
                                  max_tokens: int = 2000) -> str:
        """
        Генерирует ответ с использованием OpenAI API

        Args:
            system_prompt: Системный промпт
            user_prompt: Пользовательский промпт
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            str: Сгенерированный текст
        """
        try:
            logger.info(f"Calling OpenAI API with model {self.model}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content
            return content

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise e

    async def generate_diet_plan(self,
                                 user_data: Dict[str, Any],
                                 days: int = 7,
                                 product_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Генерирует план диеты с использованием OpenAI

        Args:
            user_data: Данные пользователя
            days: Количество дней для плана
            product_list: Список доступных продуктов

        Returns:
            Dict[str, Any]: План диеты
        """
        try:
            # Формируем промпты для генерации диеты
            system_prompt = create_diet_system_prompt(product_list)
            user_prompt = create_diet_user_prompt(user_data, days)

            # Вызываем OpenAI API
            response = await self.generate_completion(system_prompt, user_prompt)

            # Парсим и валидируем результат
            try:
                diet_plan = json.loads(response)
                return diet_plan
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                return {"error": "Failed to parse diet plan response"}

        except Exception as e:
            logger.error(f"Error generating diet plan: {str(e)}")
            return {"error": str(e)}

    async def answer_nutrition_question(self,
                                        user_id: str,
                                        question: str) -> str:
        """
        Отвечает на вопрос о питании с использованием OpenAI

        Args:
            user_id: ID пользователя
            question: Вопрос о питании

        Returns:
            str: Ответ на вопрос
        """
        try:
            # Получаем базовый системный промпт для вопросов о питании
            base_system_prompt = create_nutrition_question_prompt()

            # Получаем промпт с командами
            commands_prompt = get_bot_commands_prompt()

            # Объединяем промпты
            system_prompt = f"{base_system_prompt}\n\n{commands_prompt}"

            # Вызываем OpenAI API
            response = await self.generate_completion(system_prompt, question)

            return response.strip()

        except Exception as e:
            logger.error(f"Error answering nutrition question: {str(e)}")
            return f"Извините, произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте еще раз позже."

    async def create_shopping_list(self,
                                   diet_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Создает список покупок на основе плана диеты

        Args:
            diet_plan: План диеты

        Returns:
            List[Dict[str, Any]]: Список покупок
        """
        try:
            # Получаем промпты для списка покупок
            system_prompt, user_prompt = create_shopping_list_prompt(diet_plan)

            # Вызываем OpenAI API
            response = await self.generate_completion(system_prompt, user_prompt)

            # Парсим JSON-ответ
            try:
                shopping_list = json.loads(response)
                return shopping_list
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response for shopping list: {response}")
                return []

        except Exception as e:
            logger.error(f"Error creating shopping list: {str(e)}")
            return []

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

    async def update_short_diet_plan(self,
                               short_diet_plan: Dict[str, Any],
                               update_request: str) -> Dict[str, Any]:
        """
        Обновляет краткий план диеты на основе запроса пользователя

        Args:
            short_diet_plan: Текущий краткий план диеты
            update_request: Запрос пользователя на изменение плана

        Returns:
            Dict[str, Any]: Обновленные дни плана и комментарий
        """
        try:
            system_prompt = create_short_diet_system_prompt()
            user_prompt = update_short_diet_user_prompt(update_request, short_diet_plan)

            history_messages = []

            # Проверяем наличие метаданных генерации
            if "diet_generation_metadata" in short_diet_plan and all(key in short_diet_plan["diet_generation_metadata"]
                                                               for key in ["system_prompt", "user_prompt", "response"]):
                metadata = short_diet_plan["diet_generation_metadata"]
                # Создаем упрощенную версию плана диеты для истории сообщений
                simplified_diet_plan = self.create_simplified_diet_plan(short_diet_plan)

                history_messages = [
                    # {"role": "system", "content": metadata["system_prompt"]},
                    {"role": "user", "content": metadata["user_prompt"]},
                    # {"role": "assistant", "content": metadata["response"]},
                    {"role": "assistant", "content": json.dumps(simplified_diet_plan, ensure_ascii=False)},
                ]

            response = await self.generate_completion(system_prompt, user_prompt, history_messages, 1.5)

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
    def create_simplified_diet_plan(self, full_diet_plan: Dict[str, Any]):
        """
        Создает упрощенную версию плана диеты для уменьшения количества токенов.

        Args:
            full_diet_plan (dict): Полный план диеты

        Returns:
            dict: Упрощенный план диеты, содержащий только базовую структуру и названия блюд
        """
        simplified_plan = {
            "user_id": full_diet_plan.get("user_id", ""),
            "start_date": full_diet_plan.get("start_date", ""),
            "end_date": full_diet_plan.get("end_date", ""),
            "daily_plans": {}
        }

        # Обрабатываем планы по дням
        for date, day_plan in full_diet_plan.get("daily_plans", {}).items():
            simplified_day = {
                "meals": []
            }

            # Добавляем только тип и название для каждого приема пищи
            for meal in day_plan.get("meals", []):
                simplified_meal = {
                    "type": meal.get("type", ""),
                    "title": meal.get("title", "")
                }
                simplified_day["meals"].append(simplified_meal)

            simplified_plan["daily_plans"][date] = simplified_day

        return simplified_plan