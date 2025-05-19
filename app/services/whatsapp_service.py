import asyncio
import json
import logging
import re
import traceback
from datetime import datetime, timedelta
from enum import Enum
from random import uniform
from typing import Dict, Any, List, Optional

import pytz
from twilio.rest import Client

from app.db.firebase import firebase_client
from app.localization.messages import DietMessages
from app.services.diet import diet_service

from config import settings

logger = logging.getLogger(__name__)

# Инициализация Twilio клиента для WhatsApp API
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


class MessageType(str, Enum):
    TEXT = "text"
    MEDIA = "media"
    LOCATION = "location"
    CONTACT = "contact"
    INTERACTIVE = "interactive"
    BUTTON = "button"
    TEMPLATE = "template"


class WhatsAppService:
    """Сервис для работы с WhatsApp API"""

    def __init__(self):
        self.from_phone_number = settings.TWILIO_PHONE_NUMBER
        self.messages = DietMessages()
        # хранилище для неотправленных сообщений
        self.pending_messages = {}  # {phone_number: [(message_id, message_text, timestamp)]}

    async def initialize(self):
        """Инициализация сервиса при запуске, включая отправку отложенных сообщений"""
        try:
            logger.info("Initializing WhatsApp service...")

            logger.info("WhatsApp service initialization completed")
        except Exception as e:
            logger.error(f"Error initializing WhatsApp service: {str(e)}")


        # метод для записи отправленного сообщения
    async def _record_sent_message(self, phone_number: str, message_id: str, message_text: str):
        try:
            firebase_client.add_document("sent_messages", {
                "phone_number": phone_number,
                "message_id": message_id,
                "message_text": message_text,
                "status": "sent",
                "timestamp": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            })
        except Exception as e:
            logger.error(f"Ошибка при записи отправленного сообщения: {str(e)}")

    # метод для записи неотправленного сообщения
    async def _record_pending_message(self, phone_number: str, message_text: str, error_type: str = "unknown",
                                      onboarding_step: str = None):
        """Сохраняет неотправленное сообщение в базе данных с информацией о шаге онбординга"""
        try:
            # Проверяем, возможно это сообщение о повторной отправке
            is_resend_message = message_text.startswith("📳 ")
            is_error_message = message_text.startswith("❌ ")

            # Если это уже попытка переотправки или сообщение об ошибке,
            # не записываем его снова, чтобы избежать зацикливания
            if is_resend_message or is_error_message:
                logger.info("Skipping recording resend/error message to prevent loops")
                return

            # Проверяем, есть ли уже такое сообщение в pending статусе
            # Сначала получаем все сообщения для этого номера телефона
            existing_messages = firebase_client.query_documents(
                "pending_messages",
                "phone_number", "==", phone_number
            )

            # Фильтруем, чтобы найти сообщения с таким же текстом и статусом pending
            duplicate_messages = [
                msg for msg in existing_messages
                if msg.get("status") == "pending" and msg.get("message_text") == message_text
            ]

            # Текущие дата и время
            now = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()

            if duplicate_messages:
                # Если нашли дубликат, просто обновляем его, увеличивая счетчик попыток
                duplicate = duplicate_messages[0]
                firebase_client.update_document(
                    "pending_messages",
                    duplicate.get("id"),
                    {
                        "attempts": duplicate.get("attempts", 1) + 1,
                        "last_attempt": now,
                        "error_type": error_type,  # Обновляем тип ошибки
                        "onboarding_step": onboarding_step  # Сохраняем шаг онбординга
                    }
                )
                logger.info(
                    f"Updated existing pending message instead of creating duplicate (id: {duplicate.get('id')})")
            else:
                # Если дубликата нет, создаем новую запись
                new_message = {
                    "phone_number": phone_number,
                    "message_text": message_text,
                    "status": "pending",
                    "error_type": error_type,
                    "attempts": 1,
                    "timestamp": now,
                    "last_attempt": now
                }

                logger.info(f"Created new pending message record for {phone_number}")

                # Добавляем шаг онбординга, если он указан
                if onboarding_step:
                    new_message["onboarding_step"] = onboarding_step

                firebase_client.add_document("pending_messages", new_message)
                logger.info(f"Created new pending message record for {phone_number}")

        except Exception as e:
            logger.error(f"Ошибка при записи неотправленного сообщения: {str(e)}")


    async def _get_last_processed_message(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Получает последнее обработанное сообщение пользователя"""
        messages = firebase_client.query_documents(
            "processed_messages", "phone_number", "==", phone_number
        )
        if not messages:
            return None

        # Сортируем по времени и берем последнее
        return sorted(
            messages,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[0]

    async def _recover_conversation(self, phone_number: str, last_message: Dict[str, Any]) -> None:
        """Восстанавливает контекст диалога после разрыва"""
        # Получаем пользователя
        users = firebase_client.query_documents("users", "phone_number", "==", phone_number)
        if not users:
            return

        user = users[0]
        user_id = user.get("id")

        # Если пользователь в процессе онбординга
        if not user.get("is_onboarding_completed", True):
            step = user.get("onboarding_step", "welcome")
            message = f"Кажется, у нас был небольшой разрыв в общении. Продолжим настройку? {self._get_onboarding_step_message(step)}"
            await self.send_message(phone_number, message)
        else:
            # Если у пользователя был активный диалог
            last_text = last_message.get("message_text", "")
            time_diff = datetime.now(pytz.timezone(settings.TIMEZONE)) - datetime.fromisoformat(
                last_message["timestamp"])

            if time_diff > timedelta(hours=6):
                await self.send_message(
                    phone_number,
                    "Рад снова тебя видеть! Чем я могу помочь сегодня? Напиши 'план' чтобы увидеть свой текущий план питания или 'диета' чтобы создать новый план."
                )

    # Добавим метод для фоновой генерации полного плана
    async def _generate_full_diet_plan(self, user_id: str, short_plan_id: str):
        """
        Фоновая задача для генерации полного плана диеты

        Args:
            user_id: ID пользователя
            short_plan_id: ID короткого плана
        """
        try:
            # Получаем данные пользователя
            user = firebase_client.get_document("users", user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return

            phone_number = user.get("phone_number")

            # Генерируем полный план
            full_plan = await diet_service.generate_full_diet_plan(short_plan_id)

            if full_plan and "error" not in full_plan:
                # Отправляем уведомление пользователю
                await self.send_message(
                    phone_number,
                    "🎉 Полная версия вашего плана питания готова! Вы можете посмотреть детальную информацию о каждом дне, рецепты и сформировать список покупок."
                )

                # Отправляем сводку плана
                diet_summary, commands = diet_service.get_diet_summary(full_plan)
                await self.send_message(phone_number, diet_summary)
                await self.send_message(phone_number, commands)
            else:
                error_msg = full_plan.get("error",
                                          "Неизвестная ошибка") if full_plan else "Не удалось создать полный план диеты"
                logger.error(f"Error generating full diet plan: {error_msg}")

                await self.send_message(
                    phone_number,
                    "К сожалению, произошла ошибка при создании полной версии плана. Пожалуйста, попробуйте позже или обратитесь в поддержку."
                )

        except Exception as e:
            logger.error(f"Error in _generate_full_diet_plan: {str(e)}")

    async def _retry_with_backoff(self, func, *args, max_retries=3, initial_delay=1,
                                  max_delay=10, backoff_factor=2, **kwargs):
        """Функция для повторных попыток с экспоненциальной задержкой"""
        retries = 0
        delay = initial_delay

        while retries < max_retries:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    logger.error(f"Все попытки исчерпаны ({max_retries}). Последняя ошибка: {str(e)}")
                    return {"error": f"Не удалось выполнить операцию после {max_retries} попыток: {str(e)}"}

                # Добавляем случайный джиттер для предотвращения одновременных запросов
                jitter = uniform(0, 0.1 * delay)
                wait_time = min(delay + jitter, max_delay)

                logger.warning(
                    f"Попытка {retries}/{max_retries} не удалась: {str(e)}. Повтор через {wait_time:.2f} сек.")
                await asyncio.sleep(wait_time)

                # Увеличиваем задержку для следующей попытки
                delay = min(delay * backoff_factor, max_delay)

    def _log_error_with_context(self, message, exception=None, context=None):
        """Расширенное логирование ошибок с контекстом"""
        error_details = {
            "message": message,
            "timestamp": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
            "context": context or {}
        }

        if exception:
            error_details["exception"] = str(exception)
            error_details["traceback"] = traceback.format_exc()

        logger.error(f"{message}: {json.dumps(error_details, ensure_ascii=False)}")

    def _log_network_request(self, method, url, headers=None, data=None, params=None):
        """Расширенное логирование сетевых запросов"""
        request_info = {
            "method": method,
            "url": url,
            "timestamp": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
        }

        if headers:
            # Удаляем конфиденциальную информацию
            safe_headers = {k: v for k, v in headers.items() if "key" not in k.lower() and "token" not in k.lower()}
            request_info["headers"] = safe_headers

        if params:
            request_info["params"] = params

        if data:
            # Ограничиваем размер логируемых данных
            data_preview = str(data)[:500] + "..." if len(str(data)) > 500 else str(data)
            request_info["data_preview"] = data_preview

        logger.debug(f"Network request: {json.dumps(request_info, ensure_ascii=False)}")



# Создаем экземпляр сервиса WhatsApp
whatsapp_service = WhatsAppService()
