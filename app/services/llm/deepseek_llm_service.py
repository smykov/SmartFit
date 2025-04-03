import asyncio
import logging
from datetime import datetime

import aiohttp
import pytz
import requests
import json
from typing import Dict, Any, List, Optional

from app.db.firebase import firebase_client
from app.services.llm.base_llm_service import BaseLLMService
from app.templates.formatting_helpers import clean_json_from_markdown
from app.templates.prompts import create_diet_system_prompt, create_diet_user_prompt, \
    create_nutrition_question_prompt, get_bot_commands_prompt, update_diet_user_prompt, create_short_diet_system_prompt, \
    update_short_diet_user_prompt, create_shopping_list_user_prompt, create_shopping_list_system_prompt
from config import settings

logger = logging.getLogger(__name__)


class DeepSeekLLMService(BaseLLMService):
    """Сервис для работы с DeepSeek API"""

    def __init__(self, api_key: str, model: str = "deepseek-chat", api_base: str = "https://api.deepseek.com"):
        """
        Инициализация сервиса DeepSeek

        Args:
            api_key: Ключ API для DeepSeek
            model: Модель для использования (по умолчанию deepseek-chat)
            api_base: Базовый URL API
        """
        self.api_key = api_key

        # Проверка поддерживаемых моделей с их ограничениями
        self.MODEL_LIMITS = {
            "deepseek-chat": {"max_tokens": 8192},
            "deepseek-reasoner": {"max_tokens": 8192}
        }

        if model not in self.MODEL_LIMITS:
            logger.warning(f"Неподдерживаемая модель: {model}, используется deepseek-chat")
            model = "deepseek-chat"

        self.model = model
        self.api_base = api_base
        self.model_limit = self.MODEL_LIMITS[model]
        logger.info(f"Инициализирован DeepSeek LLM сервис с моделью {model}")

    async def generate_completion(self,
                                  system_prompt: str,
                                  user_prompt: str,
                                  history_messages: Optional[List[Dict[str, str]]] = None,
                                  temperature: float = 1.3,
                                  max_tokens: int = 8192) -> str:
        """
        Генерирует ответ с использованием DeepSeek API
        Args:
            system_prompt: Системный промпт. При наличии history_messages системный промпт будет проигнорирован, если в истории уже есть системный промпт.
            user_prompt: Пользовательский промпт
            history_messages: Предыдущие промпты
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            str: Сгенерированный текст
        """
        try:
            logger.info(f"Calling DeepSeek API with model {self.model}")

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            # Формируем список сообщений
            messages = []

            # Проверяем, есть ли системное сообщение в истории и перемещаем его в начало
            has_system_prompt = False
            system_message = {"role": "system", "content": system_prompt}

            if history_messages:
                # Ищем системное сообщение в истории
                for i, msg in enumerate(history_messages):
                    if msg.get("role") == "system":
                        has_system_prompt = True
                        system_message = msg
                        # Удаляем системное сообщение из истории, чтобы добавить его в начало
                        history_messages_copy = history_messages.copy()
                        history_messages_copy.pop(i)
                        history_messages = history_messages_copy
                        break

            # Добавляем системное сообщение в начало
            if has_system_prompt:
                messages.append(system_message)
            else:
                messages.append({"role": "system", "content": system_prompt})

            # Добавляем оставшуюся историю сообщений
            if history_messages:
                messages.extend(history_messages)

            # Добавляем новый пользовательский запрос в конец
            messages.append({"role": "user", "content": user_prompt})

            # Применяем ограничения модели
            model_max_tokens = self.model_limit["max_tokens"]
            actual_max_tokens = min(max_tokens, model_max_tokens)

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": actual_max_tokens,
            }
            # Удаляем неиспользуемые параметры для упрощения запроса
            # и добавляем только действительно нужные
            if temperature != 1.0:
                payload["temperature"] = temperature

            # Для больших запросов можно добавить опцию потоковой обработки
            if actual_max_tokens > 2000:
                payload["stream"] = False  # Выключаем потоковую обработку для больших запросов

            # Определяем, требуется ли формат JSON в ответе
            requires_json = any("json" in msg.get("content", "").lower() for msg in messages)
            # Добавляем response_format только если в промпте есть упоминание о json
            if requires_json:
                payload["response_format"] = {"type": "json_object"}

            # Логирование для отладки (без полного содержимого промптов)
            log_message_roles = [f"{i}: {msg['role']}" for i, msg in enumerate(messages)]
            logger.info(f"Message structure: {log_message_roles}")

            # Логируем отправляемый запрос (без API ключа)
            log_payload = payload.copy()
            log_payload["model"] = f"{self.model} (API base: {self.api_base})"
            logger.info(f"DeepSeek request payload: {json.dumps(log_payload, ensure_ascii=False)}")

            try:
                # Устанавливаем таймаут
                timeout = 600  # Увеличиваем таймаут до 5 минут для сложных запросов

                # Используем асинхронные запросы для лучшей обработки таймаутов
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                            f"{self.api_base}/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=timeout
                    ) as response:
                        # Логируем статус ответа
                        logger.info(f"DeepSeek API response status: {response.status}")
                        # Получаем текст ответа даже при ошибке
                        response_text = await response.text()
                        logger.info(f"Full DeepSeek API response: {response_text}")

                        # Затем проверяем статус
                        if response.status >= 400:
                            error_details = {}
                            try:
                                error_details = json.loads(response_text)
                            except:
                                error_details = {"raw_text": response_text}

                            logger.error(f"DeepSeek API error details: {json.dumps(error_details)}")
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status,
                                message=f"DeepSeek API error: {response_text}"
                            )
                        # Проверяем статус ответа
                        response.raise_for_status()

                        # Получаем текст ответа
                        response_text = await response.text()

                        # Логируем размер ответа
                        logger.info(f"DeepSeek API response size: {len(response_text)} bytes")
                        logger.info(f"Raw DeepSeek API response: {response_text}")

                        # Парсим JSON ответ
                        try:
                            response_json = json.loads(response_text)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse DeepSeek API response as JSON: {str(e)}")
                            logger.info(f"Response text: {response_text}")
                            # Возвращаем текст ответа как есть, если не удалось распарсить JSON
                            return response_text

                        # Получаем содержимое из ответа
                        if "choices" in response_json and len(response_json["choices"]) > 0:
                            if "message" in response_json["choices"][0] and "content" in response_json["choices"][0][
                                "message"]:
                                content = response_json["choices"][0]["message"]["content"]

                                # Логируем начало ответа для отладки
                                if content:
                                    logger.info(f"DeepSeek response content (truncated): {content[:100]}...")
                                else:
                                    logger.warning("Empty content in DeepSeek response")

                                return content
                            else:
                                logger.error("Unexpected DeepSeek response structure: missing 'message' or 'content'")
                                logger.info(f"Response JSON: {json.dumps(response_json)}")
                                return response_text  # Возвращаем весь текст как есть
                        else:
                            logger.error("Unexpected DeepSeek response structure: missing 'choices'")
                            logger.info(f"Response JSON: {json.dumps(response_json)}")
                            return response_text  # Возвращаем весь текст как есть

            except asyncio.TimeoutError:
                logger.error(f"DeepSeek API request timed out after {timeout} seconds")
                # Возвращаем сообщение об ошибке вместо исключения
                return f"Error: DeepSeek API request timed out after {timeout} seconds"
            except aiohttp.ClientResponseError as e:
                logger.error(f"DeepSeek API HTTP error: {str(e)}")
                # Обрабатываем ошибку и возвращаем информативное сообщение
                return f"Error: DeepSeek API HTTP error {e.status}: {e.message}"
            except aiohttp.ClientError as e:
                logger.error(f"DeepSeek API client error: {str(e)}")
                return f"Error: DeepSeek API client error: {str(e)}"
        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {str(e)}")
            # Возвращаем сообщение об ошибке вместо поднятия исключения
            return f"Error: {str(e)}"

    async def generate_diet_plan(self,
                                 user_data: Dict[str, Any],
                                 days: int = 7,
                                 product_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Генерирует план диеты с использованием DeepSeek

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

            # Добавляем дополнительную инструкцию для возврата JSON
            system_prompt += "\nВажно: Вернуть только валидный JSON без дополнительного текста."

            # Вызываем DeepSeek API
            response = await self.generate_completion(system_prompt, user_prompt)

            # Логируем полученный ответ для отладки
            logger.info(f"Raw DeepSeek response: {response}")

            # Проверяем, не пустой ли ответ
            if not response or response.strip() == "":
                logger.error("Empty response from DeepSeek API")
                # Попытка использовать заглушку или резервный сервис
                try:
                    from app.services.mock_diet_service import mock_diet_service
                    logger.info("Falling back to mock diet service")
                    return await mock_diet_service.generate_diet_plan(user_data, days)
                except Exception as mock_error:
                    logger.error(f"Failed to use mock service: {str(mock_error)}")
                    return {"error": "Empty response from DeepSeek API"}

            # Очищаем ответ от маркдауна если они есть
            response_clean = clean_json_from_markdown(response)

            # Парсим и валидируем результат
            try:
                diet_plan = json.loads(response_clean)

                # Дополнительная проверка структуры ответа
                if not isinstance(diet_plan, dict):
                    logger.error(f"Unexpected response format: {type(diet_plan)}")
                    return {"error": "Invalid diet plan format"}

                # Проверка на наличие минимальных необходимых полей
                required_fields = ["daily_plans"]
                missing_fields = [field for field in required_fields if field not in diet_plan]

                if missing_fields:
                    logger.error(f"Missing required fields in diet plan: {missing_fields}")
                    return {"error": f"Missing required fields: {', '.join(missing_fields)}"}

                # Добавляем метаданные о генерации
                diet_plan["diet_generation_metadata"] = {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "response": response
                }

                return diet_plan
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.info(f"Raw response: {response}")

                # Попытка использовать заглушку или резервный сервис
                try:
                    from app.services.mock_diet_service import mock_diet_service
                    logger.info("Falling back to mock diet service after JSON parsing error")
                    return await mock_diet_service.generate_diet_plan(user_data, days)
                except Exception as mock_error:
                    logger.error(f"Failed to use mock service: {str(mock_error)}")
                    return {"error": "Failed to parse diet plan response"}

        except Exception as e:
            logger.error(f"Error generating diet plan: {str(e)}")

            # Попытка использовать заглушку или резервный сервис
            try:
                from app.services.mock_diet_service import mock_diet_service
                logger.info("Falling back to mock diet service after exception")
                return await mock_diet_service.generate_diet_plan(user_data, days)
            except Exception as mock_error:
                logger.error(f"Failed to use mock service: {str(mock_error)}")
                return {"error": str(e)}

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
                # Создаем упрощенную версию плана диеты для истории сообщений
                simplified_diet_plan = self.create_simplified_diet_plan(diet_plan)

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

    async def answer_nutrition_question(self,
                                        user_id: str,
                                        question: str) -> str:
        """
        Отвечает на вопрос о питании с использованием DeepSeek

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

            # Логируем system_prompt для отладки
            logger.info(f"Raw DeepSeek system_prompt: {system_prompt[:1500]}...")

            # Вызываем DeepSeek API
            response = await self.generate_completion(system_prompt, question)

            # Логируем полученный ответ для отладки
            logger.info(f"Raw DeepSeek response: {response}...")

            return response.strip()

        except Exception as e:
            logger.error(f"Error answering nutrition question: {str(e)}")
            return f"Извините, произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте еще раз позже."

    async def create_shopping_list(self,
                                   diet_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Создает список покупок на основе плана диеты
TODO добавить отправку как первые сообщения для кеша стсьемный промт для генерации диеты и ответ ии с диетой, чтобы он кешировался и ответ был с учетом плана питания и данными пользователя
        Args:
            diet_plan: План диеты

        Returns:
            List[Dict[str, Any]]: Список покупок
        """
        try:
            # Получаем промпты для списка покупок
            system_prompt = create_shopping_list_system_prompt()
            user_prompt = create_shopping_list_user_prompt(diet_plan)

            # Добавляем дополнительную инструкцию для возврата JSON
            system_prompt += "\nВажно: Вернуть только валидный JSON-массив без дополнительного текста."
            logger.info(f"Raw DeepSeek system_prompt: {system_prompt[:1500]}...")
            logger.info(f"Raw DeepSeek user_prompt: {user_prompt[:1500]}...")

            # Вызываем DeepSeek API
            response = await self.generate_completion(system_prompt, user_prompt)
            logger.info(f"Raw DeepSeek response: {response}...")

            # Очищаем ответ от маркдауна если они есть
            response = clean_json_from_markdown(response)

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
