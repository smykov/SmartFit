# app/services/llm/enhanced_deepseek_llm_service.py

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional

import aiohttp

from app.services.llm.base_llm_service import (
    BaseLLMService, LLMServiceError, LLMTimeoutError,
    LLMParseError, LLMServerError
)
from app.services.llm.model_config import (
    DeepSeekModel, DeepSeekModelManager, ModelRetryConfig
)
from app.services.messaging.interfaces.message_interface import IMessengerService
from app.templates.formatting_helpers import clean_json_from_markdown
from app.templates.prompts import (
    create_nutrition_question_prompt, get_bot_commands_prompt,
    update_full_diet_user_prompt, create_shopping_list_user_prompt,
    create_shopping_list_system_prompt, create_full_diet_system_prompt
)
from config import settings

logger = logging.getLogger(__name__)


class DeepSeekLLMService(BaseLLMService):
    """
    Улучшенный сервис для работы с DeepSeek API с поддержкой множественных моделей
    и автоматическим фолбеком при ошибках
    """

    def __init__(self,
                 messenger_service: IMessengerService,
                 api_key: str,
                 api_base: str = "https://api.deepseek.com",
                 model_manager: Optional[DeepSeekModelManager] = None):
        """
        Инициализация улучшенного сервиса DeepSeek

        Args:
            messenger_service: Сервис для отправки сообщений
            api_key: Ключ API для DeepSeek
            api_base: Базовый URL API
            model_manager: Менеджер конфигураций моделей
        """
        self.api_key = api_key
        self.api_base = api_base
        self.messenger_service = messenger_service

        # Инициализируем менеджер моделей
        self.model_manager = model_manager or DeepSeekModelManager.from_settings(settings)

        # Кеш для активных сессий (для оптимизации)
        self._session_cache = {}

        logger.info(f"Инициализирован улучшенный DeepSeek LLM сервис с моделями: "
                    f"{[model.value for model in DeepSeekModel]}")

    async def generate_completion(self,
                                  system_prompt: str,
                                  user_prompt: str,
                                  history_messages: Optional[List[Dict[str, str]]] = None,
                                  temperature: float = 1.3,
                                  max_tokens: Optional[int] = None,
                                  model: Optional[str] = None) -> str:
        """
        Генерирует ответ с использованием DeepSeek API с поддержкой фолбека

        Args:
            system_prompt: Системный промпт
            user_prompt: Пользовательский промпт
            history_messages: Предыдущие промпты
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            model: Конкретная модель ('smart' для умной модели, None для дефолтной)

        Returns:
            str: Сгенерированный текст
        """
        # Определяем модель для использования
        target_model = self._resolve_model(model)

        # Пытаемся выполнить запрос с основной моделью
        try:
            return await self._generate_with_model(
                target_model, system_prompt, user_prompt,
                history_messages, temperature, max_tokens
            )
        except (LLMServiceError, LLMTimeoutError, LLMParseError, LLMServerError) as e:
            # Если была ошибка и мы не используем дефолтную модель, пробуем фолбек
            fallback_model = target_model.get_fallback_model()

            if fallback_model != target_model:
                logger.warning(
                    f"Ошибка с моделью {target_model.value}: {str(e)}. "
                    f"Переключаемся на фолбек модель {fallback_model.value}"
                )

                # Отправляем уведомление в debug чат
                await self._notify_fallback(target_model, fallback_model, str(e))

                try:
                    return await self._generate_with_model(
                        fallback_model, system_prompt, user_prompt,
                        history_messages, temperature, max_tokens
                    )
                except Exception as fallback_error:
                    logger.error(
                        f"Фолбек модель {fallback_model.value} также завершилась с ошибкой: {str(fallback_error)}")
                    # Если и фолбек не сработал, бросаем исходную ошибку
                    raise e
            else:
                # Если уже используется дефолтная модель, просто поднимаем ошибку
                raise e

    def _resolve_model(self, model_hint: Optional[str]) -> DeepSeekModel:
        """
        Определяет модель для использования на основе подсказки

        Args:
            model_hint: Подсказка модели ('smart' или None)

        Returns:
            DeepSeekModel: Модель для использования
        """
        if model_hint == "smart":
            return DeepSeekModel.get_smart()
        elif model_hint is None:
            return DeepSeekModel.get_default()
        else:
            # Пытаемся найти модель по прямому значению
            try:
                return DeepSeekModel(model_hint)
            except ValueError:
                logger.warning(f"Неизвестная модель '{model_hint}', используется дефолтная")
                return DeepSeekModel.get_default()

    async def _generate_with_model(self,
                                   model: DeepSeekModel,
                                   system_prompt: str,
                                   user_prompt: str,
                                   history_messages: Optional[List[Dict[str, str]]] = None,
                                   temperature: float = 1.3,
                                   max_tokens: Optional[int] = None) -> str:
        """
        Выполняет генерацию с конкретной моделью с учетом её настроек повторов
        """
        model_config = self.model_manager.get_config(model)
        retry_config = model_config.retry_config

        # Применяем ограничения модели для токенов
        if max_tokens is None:
            actual_max_tokens = model_config.max_tokens
        else:
            actual_max_tokens = min(max_tokens, model_config.max_tokens)

        retry_count = 0
        last_exception = None

        while retry_count <= retry_config.max_retries:
            try:
                return await self._make_api_request(
                    model, system_prompt, user_prompt, history_messages,
                    temperature, actual_max_tokens
                )

            except asyncio.TimeoutError as e:
                last_exception = LLMTimeoutError(
                    f"Превышено время ожидания для модели {model.value} ({retry_config.timeout} сек)"
                )

            except (LLMServerError, LLMParseError) as e:
                last_exception = e

                # Для определенных ошибок пропускаем повторы
                if isinstance(e, LLMServerError) and e.status_code not in [503, 502, 500]:
                    logger.error(f"Критическая ошибка для модели {model.value}: {e.status_code}")
                    raise e

            except Exception as e:
                last_exception = LLMServiceError(f"Неожиданная ошибка для модели {model.value}: {str(e)}")

            # Увеличиваем счетчик и проверяем, нужна ли еще попытка
            retry_count += 1
            if retry_count <= retry_config.max_retries:
                delay = retry_config.get_delay(retry_count - 1)
                logger.warning(
                    f"Повторная попытка {retry_count}/{retry_config.max_retries} "
                    f"для модели {model.value} через {delay:.1f} сек"
                )
                await asyncio.sleep(delay)

        # Все попытки исчерпаны
        logger.error(f"Все попытки исчерпаны для модели {model.value}")
        raise last_exception or LLMServiceError(f"Неизвестная ошибка для модели {model.value}")

    async def _make_api_request(self,
                                model: DeepSeekModel,
                                system_prompt: str,
                                user_prompt: str,
                                history_messages: Optional[List[Dict[str, str]]] = None,
                                temperature: float = 1.3,
                                max_tokens: int = 8192) -> str:
        """
        Выполняет непосредственный запрос к API
        """
        model_config = self.model_manager.get_config(model)

        logger.info(f"Выполняется запрос к DeepSeek API с моделью {model.value}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Формируем сообщения
        messages = self._build_messages(system_prompt, user_prompt, history_messages)

        # Формируем payload
        payload = {
            "model": model_config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Добавляем JSON режим если поддерживается и требуется
        requires_json = any("json" in msg.get("content", "").lower() for msg in messages)
        if requires_json and model_config.supports_json_mode:
            payload["response_format"] = {"type": "json_object"}

        # Логирование для отладки
        await self._log_request(model, payload)

        # Выполняем запрос
        timeout = aiohttp.ClientTimeout(total=model_config.retry_config.timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                    f"{self.api_base}/v1/chat/completions",
                    headers=headers,
                    json=payload
            ) as response:
                return await self._process_response(model, response)

    def _build_messages(self,
                        system_prompt: str,
                        user_prompt: str,
                        history_messages: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """Формирует список сообщений для API"""
        messages = []

        # Обработка системного промпта и истории
        system_message = {"role": "system", "content": system_prompt}

        if history_messages:
            # Ищем системное сообщение в истории
            for i, msg in enumerate(history_messages):
                if msg.get("role") == "system":
                    system_message = msg
                    # Удаляем системное сообщение из истории
                    history_messages_copy = history_messages.copy()
                    history_messages_copy.pop(i)
                    history_messages = history_messages_copy
                    break

        # Добавляем системное сообщение в начало
        messages.append(system_message)

        # Добавляем историю сообщений
        if history_messages:
            messages.extend(history_messages)

        # Добавляем новый пользовательский запрос
        messages.append({"role": "user", "content": user_prompt})

        return messages

    async def _process_response(self, model: DeepSeekModel, response) -> str:
        """Обрабатывает ответ от API"""
        logger.info(f"DeepSeek API response status: {response.status}")
        response_text = await response.text()

        # Проверка на пустой ответ
        if not response_text or response_text.strip() == "" or response_text.strip().lower() == "null":
            raise LLMParseError(
                f"Пустой ответ от DeepSeek API для модели {model.value}",
                raw_response=response_text
            )

        logger.info(f"DeepSeek API response size: {len(response_text)} bytes")

        # Проверяем статус ответа
        if response.status >= 400:
            error_details = {}
            try:
                error_details = json.loads(response_text)
            except:
                error_details = {"raw_text": response_text}

            logger.error(f"DeepSeek API error for model {model.value}: {json.dumps(error_details)}")

            raise LLMServerError(
                f"DeepSeek API HTTP error {response.status} для модели {model.value}: {response_text}",
                status_code=response.status,
                raw_response=error_details
            )

        # Парсим JSON ответ
        try:
            response_json = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for model {model.value}: {str(e)}")
            raise LLMParseError(
                f"Ошибка парсинга JSON ответа для модели {model.value}: {str(e)}",
                raw_response=response_text
            )

        # Извлекаем контент
        if "choices" not in response_json or len(response_json["choices"]) == 0:
            raise LLMParseError(
                f"Некорректная структура ответа для модели {model.value}: отсутствует 'choices'",
                raw_response=response_json
            )

        choice = response_json["choices"][0]
        if "message" not in choice or "content" not in choice["message"]:
            raise LLMParseError(
                f"Некорректная структура ответа для модели {model.value}: отсутствует 'message' или 'content'",
                raw_response=response_json
            )

        content = choice["message"]["content"]
        if not content:
            raise LLMParseError(f"Пустой контент в ответе для модели {model.value}", raw_response=response_json)

        # Логируем ответ
        await self._log_response(model, content, response_json)

        # Применяем специальную обработку для reasoner модели
        if model == DeepSeekModel.SMART:
            return clean_json_from_markdown(content)
        else:
            return content

    async def _log_request(self, model: DeepSeekModel, payload: Dict[str, Any]) -> None:
        """Логирует запрос для отладки"""
        log_payload = payload.copy()
        log_payload["model"] = f"{model.value} (API base: {self.api_base})"
        logger.info(f"DeepSeek request payload: {json.dumps(log_payload, ensure_ascii=False)}")

        # Отправляем в debug чат
        await self.messenger_service.send_message(
            settings.TELEGRAM_DEBUG_CHAT_ID,
            f"*model:* {model.value}\n #Prompts#",
            {"bot_type": "debug", "messenger_type": "telegram"},
            "debug"
        )

        for message in payload["messages"]:
            role = message.get("role")
            content = message.get("content", "")
            truncated_content = content[:500] if len(content) > 500 else content
            await self.messenger_service.send_message(
                settings.TELEGRAM_DEBUG_CHAT_ID,
                f"*{role}*\n{truncated_content}",
                {"bot_type": "debug"},
                "debug"
            )

    async def _log_response(self, model: DeepSeekModel, content: str, response_json: Dict[str, Any]) -> None:
        """Логирует ответ для отладки"""
        logger.info(f"DeepSeek response for {model.value} (truncated): {content[:1500]}...")

        # Отправляем в debug чат
        await self.messenger_service.send_message(
            settings.TELEGRAM_DEBUG_CHAT_ID,
            f"*content ({model.value}):*\n{content}",
            {"bot_type": "debug"},
            "debug"
        )

        # Логируем reasoning_content для умной модели
        if model == DeepSeekModel.SMART and "choices" in response_json:
            choice = response_json["choices"][0]
            if "message" in choice and "reasoning_content" in choice["message"]:
                reasoning_content = choice["message"]["reasoning_content"]
                await self.messenger_service.send_message(
                    settings.TELEGRAM_DEBUG_CHAT_ID,
                    f"*reasoning_content:*\n{reasoning_content}",
                    {"bot_type": "debug"},
                    "debug"
                )

        # Логируем usage
        if "usage" in response_json:
            usage = response_json["usage"]
            await self.messenger_service.send_message(
                settings.TELEGRAM_DEBUG_CHAT_ID,
                f"*usage:*\n{json.dumps(usage)}",
                {"bot_type": "debug"},
                "debug"
            )

    async def _notify_fallback(self, failed_model: DeepSeekModel, fallback_model: DeepSeekModel, error: str) -> None:
        """Уведомляет о переключении на фолбек модель"""
        try:
            await self.messenger_service.send_message(
                settings.TELEGRAM_DEBUG_CHAT_ID,
                f"🔄 *Model Fallback*\n"
                f"Failed: {failed_model.value}\n"
                f"Fallback: {fallback_model.value}\n"
                f"Error: {error[:200]}...",
                {"bot_type": "debug"},
                "debug"
            )
        except Exception as e:
            logger.error(f"Failed to send fallback notification: {str(e)}")

    async def answer_nutrition_question(self, user_id: str, question: str) -> str:
        """Отвечает на вопрос о питании (используется дефолтная модель)"""
        try:
            base_system_prompt = create_nutrition_question_prompt()
            commands_prompt = get_bot_commands_prompt()
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
            return "Извините, произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте еще раз позже."

    async def create_shopping_list(self, diet_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Создает список покупок (используется дефолтная модель)"""
        try:
            system_prompt = create_shopping_list_system_prompt()
            user_prompt = create_shopping_list_user_prompt(diet_plan)
            system_prompt += "\nВажно: Вернуть только валидный JSON-массив без дополнительного текста."
            logger.info(f"Raw DeepSeek system_prompt: {system_prompt[:1500]}...")
            logger.info(f"Raw DeepSeek user_prompt: {user_prompt[:1500]}...")

            response = await self.generate_completion(system_prompt, user_prompt)
            logger.info(f"Raw DeepSeek response: {response}...")

            # Очищаем ответ от маркдауна если они есть
            response = clean_json_from_markdown(response)

            try:
                shopping_list = json.loads(response)
                return shopping_list
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response for shopping list: {response}")
                return []

        except Exception as e:
            logger.error(f"Error creating shopping list: {str(e)}")
            return []
