# app/services/llm/deepseek_llm_service.py

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional

import aiohttp

from app.services.llm.base_llm_service import (
    BaseLLMService, LLMServiceError, LLMTimeoutError,
    LLMParseError, LLMServerError
)
from app.services.messaging.interfaces.message_interface import IMessengerService
from app.templates.formatting_helpers import clean_json_from_markdown
from app.templates.prompts import create_nutrition_question_prompt, get_bot_commands_prompt, update_full_diet_user_prompt, \
    create_shopping_list_user_prompt, create_shopping_list_system_prompt, create_full_diet_system_prompt
from config import settings

logger = logging.getLogger(__name__)


class DeepSeekLLMService(BaseLLMService):
    """Сервис для работы с DeepSeek API"""

    def __init__(self,
                 messenger_service: IMessengerService,
                 api_key: str,
                 model: str = "deepseek-chat",
                 api_base: str = "https://api.deepseek.com",
                 timeout: int = 300,
                 max_retries: int = 2,
                 ):
        """
        Инициализация сервиса DeepSeek

        Args:
            api_key: Ключ API для DeepSeek
            model: Модель для использования (по умолчанию deepseek-chat)
            api_base: Базовый URL API
            timeout: Таймаут запроса в секундах (по умолчанию 60)
            max_retries: Максимальное количество повторных попыток при ошибке
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.messenger_service = messenger_service

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
        retry_count = 0
        while retry_count <= self.max_retries:
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

                if temperature != 1.0:
                    payload["temperature"] = temperature

                # Для больших запросов можно добавить опцию потоковой обработки
                if actual_max_tokens > 2000:
                    payload["stream"] = False  # Выключаем потоковую обработку для больших запросов

                # Определяем, требуется ли формат JSON в ответе
                requires_json = any("json" in msg.get("content", "").lower() for msg in messages)
                # Добавляем response_format только если в промпте есть упоминание о json
                if requires_json and self.model != "deepseek-reasoner":
                    payload["response_format"] = {"type": "json_object"}

                # Логирование для отладки (без полного содержимого промптов)
                log_message_roles = [f"{i}: {msg['role']}" for i, msg in enumerate(messages)]
                logger.info(f"Message structure: {log_message_roles}")

                # Логируем отправляемый запрос (без API ключа)
                log_payload = payload.copy()
                log_payload["model"] = f"{self.model} (API base: {self.api_base})"
                logger.info(f"DeepSeek request payload: {json.dumps(log_payload, ensure_ascii=False)}")

                await self.messenger_service.send_message(
                    settings.TELEGRAM_DEBUG_CHAT_ID,
                    f"*model:* {self.model}\n #Prompts#",
                    {
                        "bot_type": "debug",
                        "messenger_type": "telegram"
                    },
                    "debug"
                )

                for message in messages:
                    role = message.get("role")
                    content = message.get("content")
                    await self.messenger_service.send_message(
                        settings.TELEGRAM_DEBUG_CHAT_ID,
                        f"*{role}*\n{content:500}",
                        {
                            "bot_type": "debug"
                        },
                        "debug"
                    )

                # Устанавливаем таймаут
                timeout = aiohttp.ClientTimeout(total=self.timeout)

                # Используем асинхронные запросы для лучшей обработки таймаутов
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                            f"{self.api_base}/v1/chat/completions",
                            headers=headers,
                            json=payload
                    ) as response:
                        # Логируем статус ответа
                        logger.info(f"DeepSeek API response status: {response.status}")
                        # Получаем текст ответа даже при ошибке
                        response_text = await response.text()

                        # Проверка на пустой ответ или null
                        if not response_text or response_text.strip() == "" or response_text.strip().lower() == "null":
                            raise LLMParseError(
                                "Пустой ответ от DeepSeek API",
                                raw_response=response_text
                            )

                        logger.info(f"Full DeepSeek API response: {response_text}")

                        # Проверяем статус ответа
                        if response.status >= 400:
                            error_details = {}
                            try:
                                error_details = json.loads(response_text)
                            except:
                                error_details = {"raw_text": response_text}

                            logger.error(f"DeepSeek API error details: {json.dumps(error_details)}")

                            # Генерируем соответствующее исключение в зависимости от кода ошибки
                            if response.status == 503:
                                # Сервис недоступен, следующая попытка может быть успешной
                                raise LLMServerError(
                                    f"DeepSeek API сервис недоступен: {response_text}",
                                    status_code=response.status,
                                    raw_response=error_details
                                )
                            else:
                                # Другие ошибки HTTP
                                raise LLMServerError(
                                    f"DeepSeek API HTTP error {response.status}: {response_text}",
                                    status_code=response.status,
                                    raw_response=error_details
                                )

                        # Логируем размер ответа
                        logger.info(f"DeepSeek API response size: {len(response_text)} bytes")

                        # Парсим JSON ответ
                        try:
                            response_json = json.loads(response_text)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse DeepSeek API response as JSON: {str(e)}")
                            logger.info(f"Response text: {response_text}")
                            raise LLMParseError(
                                f"Ошибка парсинга JSON ответа: {str(e)}",
                                raw_response=response_text
                            )

                        # Получаем содержимое из ответа
                        if "choices" in response_json and len(response_json["choices"]) > 0:
                            if "message" in response_json["choices"][0] and "content" in response_json["choices"][0][
                                "message"]:
                                content = response_json["choices"][0]["message"]["content"]

                                if not content:
                                    raise LLMParseError("Пустой контент в ответе", raw_response=response_json)

                                # Логируем начало ответа для отладки
                                logger.info(f"DeepSeek response content (truncated): {content[:1500]}...")

                                await self.messenger_service.send_message(
                                    settings.TELEGRAM_DEBUG_CHAT_ID,
                                    f"*content:*\n{content}",
                                    {
                                        "bot_type": "debug"
                                    },
                                    "debug"
                                )

                                if "reasoning_content" in response_json["choices"][0]["message"]:
                                    reasoning_content = response_json["choices"][0]["message"]["reasoning_content"]
                                    await self.messenger_service.send_message(
                                        settings.TELEGRAM_DEBUG_CHAT_ID,
                                        f"*reasoning_content:*\n{reasoning_content}",
                                        {
                                            "bot_type": "debug"
                                        },
                                        "debug"
                                    )

                                if "usage" in response_json:
                                    usage = response_json["usage"]
                                    await self.messenger_service.send_message(
                                        settings.TELEGRAM_DEBUG_CHAT_ID,
                                        f"*usage:*/n{json.dumps(usage)}",
                                        {
                                            "bot_type": "debug"
                                        },
                                        "debug"
                                    )

                                if self.model == "deepseek-reasoner":
                                    # Применить специальную обработку для DeepSeek Reasoner
                                    return clean_json_from_markdown(content)
                                else:
                                    return content
                            else:
                                logger.error("Unexpected DeepSeek response structure: missing 'message' or 'content'")
                                logger.info(f"Response JSON: {json.dumps(response_json)}")
                                raise LLMParseError(
                                    "Некорректная структура ответа: отсутствует 'message' или 'content'",
                                    raw_response=response_json
                                )
                        else:
                            logger.error("Unexpected DeepSeek response structure: missing 'choices'")
                            raise LLMParseError(
                                "Некорректная структура ответа: отсутствует 'choices'",
                                raw_response=response_json
                            )

            except asyncio.TimeoutError:
                logger.error(f"DeepSeek API request timed out after {self.timeout} seconds")
                # Повышаем счетчик попыток и решаем нужно ли пробовать снова
                retry_count += 1
                if retry_count > self.max_retries:
                    raise LLMTimeoutError(
                        f"Превышено время ожидания ответа от DeepSeek API ({self.timeout} сек)"
                    )
                logger.warning(f"Повторная попытка {retry_count}/{self.max_retries}...")
                # Небольшая задержка перед следующей попыткой
                await asyncio.sleep(1)
                continue

            except (LLMServerError, LLMParseError) as e:
                # Повышаем счетчик попыток, но только для определенных ошибок
                retry_count += 1
                if isinstance(e, LLMServerError) and e.status_code == 503 and retry_count <= self.max_retries:
                    logger.warning(f"Сервис DeepSeek недоступен, повторная попытка {retry_count}/{self.max_retries}...")
                    # Задержка перед следующей попыткой
                    await asyncio.sleep(2 ** retry_count)  # Экспоненциальная задержка
                    continue
                # Если это не 503 ошибка или уже превышено максимальное количество попыток
                raise

            except Exception as e:
                logger.error(f"Error calling DeepSeek API: {str(e)}")
                raise LLMServiceError(f"Ошибка при вызове DeepSeek API: {str(e)}")

        return "{}"


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
            system_prompt = create_full_diet_system_prompt()
            user_prompt = update_full_diet_user_prompt(update_request)

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
