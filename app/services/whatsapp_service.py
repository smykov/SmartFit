import logging
from typing import Dict, Any, List, Optional, Tuple
import requests
import json
import asyncio
from random import uniform
import traceback

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from enum import Enum
import re
from datetime import datetime, date, timedelta
import pytz

from app.templates.prompts import format_help_message
from config import settings
from app.db.firebase import firebase_client
from app.services.llm import llm_service
from app.services.tracking_service import tracking_service
from app.services.diet import diet_service
from app.models.tracking import MealComplianceStatus
from app.templates.formatting_helpers import (
    format_message_with_emojis,
    translate_meal_type, translate_day_name
)
from app.localization.messages import DietMessages

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

    # TODO провести рефактор сервиса и отделить команды, уведомления и тп

    def __init__(self):
        self.from_phone_number = settings.TWILIO_PHONE_NUMBER
        self.messages = DietMessages()
        self.ONBOARDING_STEPS = [
            "welcome",
            "name",
            "age",
            "gender",
            "height",
            "current_weight",
            "target_weight",
            "activity_level",
            "weight_goal",
            "diet_preference",
            "allergies",
            "disliked_products",
            "budget",
            "complete"
        ]
        # хранилище для неотправленных сообщений
        self.pending_messages = {}  # {phone_number: [(message_id, message_text, timestamp)]}

    async def initialize(self):
        """Инициализация сервиса при запуске, включая отправку отложенных сообщений"""
        try:
            logger.info("Initializing WhatsApp service...")

            # Запускаем отправку всех неотправленных сообщений
            await self._resend_all_pending_messages()

            logger.info("WhatsApp service initialization completed")
        except Exception as e:
            logger.error(f"Error initializing WhatsApp service: {str(e)}")

    async def _resend_all_pending_messages(self):
        """Отправляет все неотправленные сообщения из базы данных с учетом шага онбординга"""
        try:
            # Получаем все неотправленные сообщения
            pending_messages = firebase_client.query_documents("pending_messages", "status", "==", "pending")

            if not pending_messages:
                logger.info("No pending messages found to resend")
                return

            logger.info(f"Found {len(pending_messages)} pending messages to resend")

            # Удаляем очевидные дубликаты перед отправкой
            # Создаем уникальные идентификаторы сообщений (телефон + текст) для поиска дубликатов
            message_ids = {}  # {unique_id: message}
            duplicates_removed = 0

            for message in pending_messages:
                phone = message.get("phone_number", "")
                text = message.get("message_text", "")
                unique_id = f"{phone}:{text}"

                if unique_id in message_ids:
                    # Это дубликат, оставляем только более раннее сообщение
                    existing_msg = message_ids[unique_id]
                    existing_time = datetime.fromisoformat(existing_msg.get("timestamp", "2100-01-01"))
                    current_time = datetime.fromisoformat(message.get("timestamp", "2100-01-01"))

                    if current_time < existing_time:
                        # Текущее сообщение старше, помечаем существующее как дубликат
                        firebase_client.delete_document("pending_messages", existing_msg.get("id"))
                        logger.info(f"Deleted duplicate pending message {message.get('id')}")
                        message_ids[unique_id] = message
                        duplicates_removed += 1
                    else:
                        # Существующее сообщение старше, помечаем текущее как дубликат
                        firebase_client.delete_document("pending_messages", message.get("id"))
                        logger.info(f"Deleted duplicate pending message {message.get('id')}")
                        duplicates_removed += 1
                else:
                    message_ids[unique_id] = message

            if duplicates_removed > 0:
                logger.info(f"Removed {duplicates_removed} duplicate pending messages")

            # Продолжаем отправку оставшихся сообщений, группируя по телефону
            unique_messages = list(message_ids.values())
            # Группируем сообщения по номеру телефона для более эффективной отправки
            messages_by_phone = {}

            for message in unique_messages:
                phone = message.get("phone_number")
                if phone not in messages_by_phone:
                    messages_by_phone[phone] = []
                messages_by_phone[phone].append(message)

            # Обрабатываем каждый номер телефона
            for phone_number, messages in messages_by_phone.items():
                # Проверяем текущий статус онбординга пользователя
                users = firebase_client.query_documents("users", "phone_number", "==", phone_number)

                current_step = None
                is_onboarding_completed = True

                if users:
                    user = users[0]
                    current_step = user.get("onboarding_step")
                    is_onboarding_completed = user.get("is_onboarding_completed", False)

                # Фильтруем сообщения на основе шага онбординга
                filtered_messages = []
                for message in messages:
                    # Если онбординг завершен, включаем все сообщения
                    if is_onboarding_completed:
                        filtered_messages.append(message)
                        continue

                    # Если онбординг не завершен, проверяем шаг сообщения
                    msg_step = message.get("onboarding_step")

                    # Если у сообщения нет шага или его шаг совпадает с текущим - включаем
                    if not msg_step or msg_step == current_step:
                        filtered_messages.append(message)

                # Сортируем по времени (от ранних к поздним)
                sorted_messages = sorted(filtered_messages, key=lambda x: x.get("timestamp", ""))

                # Лимитируем количество сообщений для одного пользователя
                max_messages_per_user = 5  # Максимум 5 сообщений за раз

                # Отправляем сообщения с небольшой задержкой между ними
                for message in sorted_messages[:max_messages_per_user]:
                    # Проверяем, не устарело ли сообщение (например, 3 дня)
                    timestamp = datetime.fromisoformat(message.get("timestamp", ""))
                    now = datetime.now(pytz.timezone(settings.TIMEZONE))

                    if (now - timestamp).total_seconds() > 259200:  # 3 дня
                        # Удаляем устаревшее сообщение
                        firebase_client.delete_document("pending_messages", message.get("id"))
                        logger.info(f"Deleted expired pending message {message.get('id')}")
                        continue

                    # Формируем сообщение с префиксом для старых сообщений
                    prefix = ""
                    if (now - timestamp).total_seconds() > 3600:  # 1 час
                        prefix = "📳 Отложенное сообщение:\n\n"

                    # Попытка отправки с сохранением информации о шаге
                    success = await self.send_message(
                        phone_number,
                        prefix + message.get("message_text", ""),
                        message.get("onboarding_step")
                    )

                    if success:
                        # Удаляем сообщение после успешной отправки
                        firebase_client.delete_document("pending_messages", message.get("id"))
                        logger.info(f"Deleted successfully sent pending message {message.get('id')}")
                    else:
                        # Увеличиваем счетчик попыток
                        firebase_client.update_document(
                            "pending_messages",
                            message.get("id"),
                            {
                                "attempts": message.get("attempts", 1) + 1,
                                "last_attempt": now.isoformat()
                            }
                        )

                        # Небольшая задержка между сообщениями
                        await asyncio.sleep(5)

                    # Задержка между пользователями для снижения нагрузки на Twilio
                    await asyncio.sleep(15)

        except Exception as e:
            logger.error(f"Error resending all pending messages: {str(e)}")

    async def _check_and_send_pending_messages(self, phone_number: str):
        """Проверяет наличие неотправленных сообщений для пользователя и пытается их отправить"""
        try:
            # Сначала получаем информацию о пользователе
            users = firebase_client.query_documents("users", "phone_number", "==", phone_number)
            if not users:
                logger.warning(f"User not found for phone number {phone_number} when checking pending messages")
                return

            user = users[0]
            current_step = user.get("onboarding_step")
            is_onboarding_completed = user.get("is_onboarding_completed", False)

            # Сначала получаем все сообщения для этого номера телефона
            all_messages = firebase_client.query_documents("pending_messages", "phone_number", "==", phone_number)

            # Отфильтровываем подходящие сообщения
            pending_messages = []
            for msg in all_messages:
                if msg.get("status") != "pending":
                    continue

                # Если онбординг завершен, отправляем все сообщения
                if is_onboarding_completed:
                    pending_messages.append(msg)
                    continue

                # Если онбординг не завершен, проверяем шаг сообщения
                msg_step = msg.get("onboarding_step")

                # Если у сообщения нет шага или его шаг совпадает с текущим - отправляем
                if not msg_step or msg_step == current_step:
                    pending_messages.append(msg)

            if not pending_messages:
                return

            # Сортируем по времени (от ранних к поздним)
            pending_messages = sorted(pending_messages, key=lambda x: x.get("timestamp", ""))

            # Ограничиваем количество отправляемых сообщений за одно взаимодействие
            max_messages = 3  # Отправляем максимум 3 сообщения за раз

            for message in pending_messages[:max_messages]:
                # Проверяем, не устарело ли сообщение (например, 3 дня)
                timestamp = datetime.fromisoformat(message.get("timestamp", ""))
                now = datetime.now(pytz.timezone(settings.TIMEZONE))

                if (now - timestamp).total_seconds() > 259200:  # 3 дня
                    # Помечаем как устаревшее
                    firebase_client.update_document(
                        "pending_messages",
                        message.get("id"),
                        {"status": "expired"}
                    )
                    continue

                # Формируем сообщение с префиксом для старых сообщений
                prefix = ""
                if (now - timestamp).total_seconds() > 3600:  # 1 час
                    prefix = "📳 Отложенное сообщение:\n\n"

                # Попытка отправки
                success = await self.send_message(
                    phone_number,
                    prefix + message.get("message_text", "")
                )

                if success:
                    # Удаляем сообщение после успешной отправки вместо изменения статуса
                    firebase_client.delete_document("pending_messages", message.get("id"))
                    logger.info(f"Deleted successfully sent pending message {message.get('id')}")
                else:
                    # Увеличиваем счетчик попыток
                    firebase_client.update_document(
                        "pending_messages",
                        message.get("id"),
                        {
                            "attempts": message.get("attempts", 1) + 1,
                            "last_attempt": now.isoformat()
                        }
                    )

                # Небольшая задержка между сообщениями, чтобы не перегружать Twilio
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Ошибка при проверке неотправленных сообщений: {str(e)}")

    async def send_message(self, to_phone: str, message: str, onboarding_step: str = None) -> bool:
        """
        Отправляет текстовое сообщение по WhatsApp

        Args:
            to_phone: Номер телефона получателя
            message: Текст сообщения
            onboarding_step: Текущий шаг онбординга, с которым связано сообщение

        Returns:
            bool: Результат отправки
        """
        try:
            # Нормализуем номер телефона (добавляем +, если его нет)
            if not to_phone.startswith('+'):
                to_phone = f"+{to_phone}"

            # Проверяем на превышение лимита длины и разбиваем сообщение при необходимости
            if len(message) > 1500:
                return await self.send_chunked_message(to_phone, message, onboarding_step)

            # Проверяем, отправлялось ли уже это сообщение в последние 5 минут
            # для предотвращения случайного дублирования при ретраях
            # ТОЛЬКО для отложенных сообщений (не для прямых команд пользователя)
            if message.startswith("📳 "):  # Отложенное сообщение
                sent_messages = firebase_client.query_documents(
                    "sent_messages",
                    "phone_number", "==", to_phone
                )

                now = datetime.now(pytz.timezone(settings.TIMEZONE))
                five_minutes_ago = (now - timedelta(minutes=5)).isoformat()

                recent_duplicates = [
                    msg for msg in sent_messages
                    if msg.get("message_text") == message and msg.get("timestamp", "") > five_minutes_ago
                ]

                if recent_duplicates:
                    logger.warning(f"Preventing duplicate message send: identical message sent within last 5 minutes")
                    return True  # Возвращаем True, чтобы не создавать pending запись

            # Отправляем сообщение через Twilio
            try:
                message_response = twilio_client.messages.create(
                    from_=f"whatsapp:{self.from_phone_number}",
                    body=message,
                    to=f"whatsapp:{to_phone}"
                )

                # Сохраняем ID отправленного сообщения
                message_id = message_response.sid
                logger.info(f"Сообщение успешно отправлено: {message_id}")

                # Записываем в базу данных информацию об отправленном сообщении
                await self._record_sent_message(to_phone, message_id, message)

                return True

            except TwilioRestException as tre:
                error_code = tre.status if hasattr(tre, 'status') else 'unknown'
                error_type = "twilio_error"

                # Особая обработка ошибок Twilio
                if error_code == 429:  # Rate limit exceeded
                    error_type = "rate_limited"
                    logger.warning(f"Превышен лимит сообщений Twilio: {str(tre)}")
                elif error_code == 400 and "exceeds the 1600 character limit" in str(tre):
                    error_type = "message_too_long"
                    logger.warning("Превышен лимит символов в сообщении, пробуем отправить по частям")
                    return await self.send_chunked_message(to_phone, message, onboarding_step)
                else:
                    logger.error(f"Ошибка Twilio при отправке сообщения: {str(tre)}")

                # Сохраняем сообщение для отложенной отправки (с проверкой на дубликаты)
                await self._record_pending_message(to_phone, message, error_type, onboarding_step)
                return False

        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {str(e)}")

            # Сохраняем неотправленное сообщение для повторной попытки
            await self._record_pending_message(to_phone, message, "general_error", onboarding_step)

            return False

    async def send_chunked_message(self, to_phone: str, message: str, onboarding_step: str = None) -> bool:
        """
        Разбивает длинное сообщение на части и отправляет последовательно

        Args:
            to_phone: Номер телефона получателя
            message: Текст сообщения
            onboarding_step: Шаг онбординга, к которому относится сообщение

        Returns:
            bool: Результат отправки
        """
        try:
            # Если сообщение короткое, отправляем как обычно
            if len(message) <= 1500:  # Оставляем запас на маркеры разделения
                return await self.send_message(to_phone, message, onboarding_step)

            # Разбиваем длинное сообщение на части
            parts = []
            current_part = ""

            # Разбиваем текст по строкам и параграфам, чтобы не разрывать предложения
            paragraphs = message.split('\n\n')
            for paragraph in paragraphs:
                lines = paragraph.split('\n')
                for line in lines:
                    # Если текущая часть + новая строка больше лимита
                    if len(current_part + line + '\n') > 1500:
                        # Если текущая часть не пуста, добавляем её в список частей
                        if current_part:
                            parts.append(current_part.strip())
                            current_part = ""

                        # Если строка сама по себе превышает лимит, разбиваем её
                        if len(line) > 1500:
                            while line:
                                parts.append(line[:1500])
                                line = line[1500:]
                        else:
                            current_part = line + '\n'
                    else:
                        current_part += line + '\n'

                # Добавляем разделитель параграфов
                current_part += '\n'

            # Добавляем последнюю часть, если она не пуста
            if current_part:
                parts.append(current_part.strip())

            # Добавляем маркеры для частей
            total_parts = len(parts)
            all_sent = True

            for idx, part in enumerate(parts):
                part_marker = f"[{idx + 1}/{total_parts}] "

                # Для первой части не добавляем маркер продолжения
                if idx == 0:
                    formatted_part = part
                else:
                    formatted_part = f"(продолжение) {part}"

                # Добавляем маркер части
                full_part = part_marker + formatted_part

                # Отправляем часть
                success = await self.send_message(to_phone, full_part, onboarding_step)

                # Если хотя бы одна часть не отправлена, запоминаем
                if not success:
                    all_sent = False

                # Добавляем небольшую задержку между отправками
                await asyncio.sleep(0.5)

            return all_sent

        except Exception as e:
            logger.error(f"Ошибка при отправке разбитого сообщения: {str(e)}")
            return False

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

    async def send_messages(self, to_phone: str, messages: List[str]) -> bool:
        """
        Отправляет несколько текстовых сообщений по WhatsApp

        Args:
            to_phone: Номер телефона получателя
            messages: Список текстовых сообщений

        Returns:
            bool: Результат отправки
        """
        try:
            # Проверяем, что список сообщений не пустой
            if not messages:
                return True

            # Отправляем каждое сообщение последовательно
            for message in messages:
                # Добавляем небольшую задержку между сообщениями для лучшего восприятия
                await self.send_message(to_phone, message)
                await asyncio.sleep(0.5)  # Небольшая задержка для лучшего пользовательского опыта

            return True

        except Exception as e:
            logger.error(f"Ошибка при отправке нескольких сообщений: {str(e)}")
            return False

    async def send_template_message(self, to_phone: str, template_name: str, params: List[str] = None) -> bool:
        """
        Отправляет шаблонное сообщение через WhatsApp Business API

        Args:
            to_phone: Номер телефона получателя
            template_name: Название шаблона
            params: Параметры для шаблона

        Returns:
            bool: Результат отправки
        """
        try:
            # Нормализуем номер телефона
            if not to_phone.startswith('+'):
                to_phone = f"+{to_phone}"

            # Для MVP упрощенно используем обычное сообщение вместо шаблона
            # В реальном проекте здесь надо использовать WhatsApp Business API для шаблонов

            # Базовые шаблоны для MVP
            templates = {
                "welcome": "👋 Привет! Добро пожаловать в GuateFit - твой персональный ассистент для контроля веса. Я помогу тебе создать план питания, который подходит именно тебе, учитывая местные продукты и твой бюджет. Давай начнем настройку! Как тебя зовут?",

                "diet_created": "🎉 Твой план питания готов! Я подобрал блюда, учитывая твои параметры и предпочтения. Посмотри план и дай мне знать, если хочешь что-то изменить.",

                "weight_reminder": "⚖️ Привет! Не забудь записать свой вес сегодня. Это поможет отслеживать прогресс. Просто напиши 'вес XX', где XX - твой вес в килограммах.",

                "water_reminder": "💧 Не забывай пить воду! Отправь 'вода X', где X - количество стаканов, которые ты выпил(а).",

                "weekly_report": "📊 Вот твой еженедельный отчет:\n{progress}\n\nОтличная работа! Продолжай в том же духе! 💪"
            }

            message_text = templates.get(template_name, "Сообщение шаблона")

            # Заменяем параметры, если они есть
            if params:
                for i, param in enumerate(params):
                    message_text = message_text.replace(f"{{{i}}}", param)

            # Отправляем сообщение
            return await self.send_message(to_phone, message_text)

        except Exception as e:
            logger.error(f"Ошибка при отправке шаблонного сообщения: {str(e)}")
            return False

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

    async def _process_regular_message(self, user: Dict[str, Any], message_text: str, message_type: str) -> Dict[
        str, Any]:
        """
        Обрабатывает обычное сообщение от пользователя

        Args:
            user: Данные пользователя
            message_text: Текст сообщения
            message_type: Тип сообщения

        Returns:
            Dict[str, Any]: Результат обработки
        """
        try:
            # Проверяем наличие ID пользователя и получаем его правильно
            if "id" not in user:
                # Если id отсутствует, попробуем найти пользователя по номеру телефона
                users = firebase_client.query_documents("users", "phone_number", "==", user.get("phone_number"))
                if users and len(users) > 0:
                    user_id = users[0].get("id")
                    if not user_id:
                        logger.error(f"Не удалось определить ID пользователя: {user.get('phone_number')}")
                        return {"success": False, "error": "User ID not found"}
                else:
                    logger.error(f"Пользователь не найден: {user.get('phone_number')}")
                    return {"success": False, "error": "User not found"}
            else:
                user_id = user["id"]

            phone_number = user.get("phone_number")

            # Обновляем время последнего взаимодействия
            firebase_client.update_document("users", user_id, {"last_interaction": "now"})

            # Проверяем специальные команды

            # Команда для записи веса
            weight_match = re.match(r'^вес\s+(\d+[.,]?\d*)$', message_text.lower())
            if weight_match:
                weight = float(weight_match.group(1).replace(',', '.'))
                await tracking_service.record_weight(user_id, weight)

                # Получаем прогресс
                progress = await tracking_service.calculate_weight_progress(user_id)

                # Формируем сообщение с прогрессом
                message = f"✅ Отлично! Я записал твой вес: {weight} кг.\n\n"

                if progress:
                    if progress.total_weight_change < 0:
                        message += f"📉 С начала ты уже сбросил {abs(progress.total_weight_change):.1f} кг "
                    else:
                        message += f"📈 С начала ты уже набрал {progress.total_weight_change:.1f} кг "

                    message += f"({abs(progress.weight_change_percentage):.1f}% от начального веса)\n\n"

                    message += f"🎯 До целевого веса осталось: {abs(progress.remaining_to_goal):.1f} кг\n"
                    message += f"📊 Ты выполнил {progress.goal_completion_percentage:.1f}% своей цели!\n\n"

                message += "Продолжай отслеживать прогресс регулярно! 💪"

                await self.send_message(phone_number, message)
                return {"success": True, "action": "weight_recorded"}

            # Команда для записи потребления воды
            water_match = re.match(r'^вода\s+(\d+[.,]?\d*)$', message_text.lower())
            if water_match:
                amount = float(water_match.group(1).replace(',', '.'))
                # Конвертируем стаканы в миллилитры (примерно 250 мл в стакане)
                ml_amount = amount * 250
                await tracking_service.record_water_intake(user_id, ml_amount)

                # Получаем статус трекинга
                status = await tracking_service.get_daily_status(user_id)

                # Формируем сообщение
                message = f"💧 Отлично! Я записал потребление воды: {amount} стаканов (~{ml_amount} мл).\n\n"

                if status:
                    message += f"Сегодня ты выпил всего: {status.current_water_intake} мл\n"
                    message += f"Это {status.water_percentage:.1f}% от дневной цели в {status.water_goal} мл\n\n"

                message += "Продолжай в том же духе! Регулярное потребление воды помогает контролировать голод и улучшает общее самочувствие."

                await self.send_message(phone_number, message)
                return {"success": True, "action": "water_recorded"}

            # Добавить проверку на команду "помощь"
            if message_text.lower() in ["помощь", "справка", "команды", "help", "ayuda", "comandos"]:
                # Отправляем отформатированное сообщение с командами
                help_message = format_help_message()
                await self.send_message(phone_number, help_message)
                return {"success": True, "action": "help_message_sent"}

            # Команды для регистрации соблюдения режима питания
            # TODO доделать через ии определять по трекингу приема пищи (пользователь будет писать обед был из рыбы и тп или пообедал рыбой и тп, а ии определять насколько совпадает с планом и давай рекомендации для корректировки в течении дня чтобы выполнить цель)
            compliance_patterns = {
                "выполнено": MealComplianceStatus.FOLLOWED,
                "частично": MealComplianceStatus.PARTIALLY,
                "заменил": MealComplianceStatus.SUBSTITUTED,
                "пропустил": MealComplianceStatus.SKIPPED
            }

            for command, status in compliance_patterns.items():
                compliance_match = re.match(fr'^{command}\s+(\w+)$', message_text.lower())
                if compliance_match:
                    meal_type_ru = compliance_match.group(1).lower()

                    # Проверка существования плана
                    diet_plan = await diet_service.get_current_diet(user_id)
                    if not diet_plan:
                        await self.send_message(
                            phone_number,
                            "У тебя пока нет активного плана питания. Напиши 'диета' для создания нового плана."
                        )
                        return {"success": False, "action": "no_diet_plan_for_compliance"}

                    # Преобразуем русское название в английское
                    meal_type_map = {
                        "завтрак": "breakfast",
                        "обед": "lunch",
                        "ужин": "dinner",
                        "перекус": "snack"
                    }

                    meal_type = meal_type_map.get(meal_type_ru)

                    if not meal_type:
                        await self.send_message(
                            phone_number,
                            "Пожалуйста, укажите корректный тип приема пищи: завтрак, обед, ужин или перекус."
                        )
                        return {"success": False, "action": "invalid_meal_type"}

                    # Получаем текущую дату
                    today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

                    # Записываем соблюдение
                    notes = None
                    alternative_meal = None

                    # Если тип "заменил", можно было бы запросить на что заменил, но для упрощения оставим None

                    result = await tracking_service.record_meal_compliance(
                        user_id,
                        today,
                        meal_type,
                        status,
                        notes,
                        alternative_meal
                    )

                    if result:
                        # Получаем общую статистику соблюдения
                        compliance_data = await tracking_service.get_diet_compliance(user_id, today)

                        # Формируем сообщение
                        meal_type_ru_display = meal_type_ru.capitalize()

                        if status == MealComplianceStatus.FOLLOWED:
                            message = f"✅ Отлично! {meal_type_ru_display} выполнен по плану."
                        elif status == MealComplianceStatus.PARTIALLY:
                            message = f"⚠️ Хорошо! {meal_type_ru_display} частично выполнен по плану."
                        elif status == MealComplianceStatus.SUBSTITUTED:
                            message = f"🔄 Понятно! {meal_type_ru_display} заменен на другое блюдо."
                        elif status == MealComplianceStatus.SKIPPED:
                            message = f"❌ Отмечено! {meal_type_ru_display} пропущен."

                        # Добавляем информацию о общем соблюдении
                        if compliance_data and "overall_score" in compliance_data:
                            message += f"\n\nОбщее соблюдение плана на сегодня: {compliance_data['overall_score']:.1f}%"

                            # Добавляем мотивацию
                            if compliance_data["overall_score"] >= 80:
                                message += "\n\n👍 Отличная работа! Продолжай в том же духе."
                            elif compliance_data["overall_score"] >= 50:
                                message += "\n\n👍 Хороший результат! Старайся следовать плану."
                            else:
                                message += "\n\n💪 Не сдавайся! Каждый день - это новая возможность."

                        await self.send_message(phone_number, message)
                        return {"success": True, "action": "compliance_recorded"}
                    else:
                        await self.send_message(
                            phone_number,
                            "Извините, произошла ошибка при записи данных о соблюдении плана. Попробуйте позже."
                        )
                        return {"success": False, "action": "compliance_record_failed"}

            # Команды для работы с планом питания
            plan_commands = {
                r'^план$': "summary",
                r'^меню': "summary",
                r'^план на сегодня$': "today",
                r'^меню на сегодня$': "today",
                r'^план\s+на\s+завтра$': "tomorrow",
                r'^меню\s+на\s+завтра$': "tomorrow",
                r'^полный план$': "full",
                r'^полное меню': "full",
                r'^список покупок$': "shopping"
            }

            for pattern, command_type in plan_commands.items():
                if re.match(pattern, message_text.lower()):
                    # Получаем текущий план диеты
                    diet_plan = await diet_service.get_current_diet(user_id)

                    if not diet_plan:
                        await self.send_message(
                            phone_number,
                            "У тебя пока нет активного плана питания. Напиши 'диета' для создания нового плана."
                        )
                        return {"success": False, "action": "no_diet_plan"}

                    if command_type == "summary":
                        # Отправляем краткую сводку плана
                        summary, commands = diet_service.get_diet_summary(diet_plan)
                        await self.send_message(phone_number, summary)
                        await self.send_message(phone_number, commands)

                        return {"success": True, "action": "diet_summary_sent"}

                    elif command_type == "today":
                        # Получаем сегодняшнюю дату
                        today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

                        # Отправляем детальный план на сегодня
                        formatted_plan = diet_service.get_day_diet_plan(diet_plan, today)
                        if not formatted_plan:
                            await self.send_message(
                                phone_number,
                                "У вас пока нет плана питания на сегодня. Напишите 'диета' для создания плана."
                            )
                            return {"success": False, "action": "no_diet_for_today"}

                        # Отправляем план
                        await self.send_message(phone_number, formatted_plan)
                        return {"success": True, "action": "diet_day_plan_sent"}

                    elif command_type == "tomorrow":
                        # Получаем завтрашнюю дату
                        tomorrow = datetime.now(pytz.timezone(settings.TIMEZONE)).date() + timedelta(days=1)

                        # Отправляем детальный план на сегодня
                        day_plan = diet_service.get_day_diet_plan(diet_plan, tomorrow)
                        await self.send_message(phone_number, day_plan)
                        return {"success": True, "action": "diet_day_plan_sent"}

                    elif command_type == "full":
                        # Отправляем полный план на все дни
                        full_plan = diet_service.get_full_diet_plan(diet_plan)
                        await self.send_messages(phone_number, full_plan)
                        return {"success": True, "action": "full_diet_plan_sent"}

                    elif command_type == "shopping":
                        # Уведомляем пользователя о начале генерации списка покупок
                        await self.send_message(
                            phone_number, self.messages.SHOPPING_LIST_GENERATION
                        )
                        # Генерируем список покупок
                        try:
                            shopping_list = await diet_service.generate_shopping_list(diet_plan["id"])

                            if shopping_list and "error" not in shopping_list:
                                # Форматируем список покупок
                                formatted_list = diet_service.format_shopping_list(shopping_list)
                                await self.send_message(phone_number, formatted_list)
                                return {"success": True, "action": "shopping_list_sent"}
                            else:
                                await self.send_message(
                                    phone_number,
                                    self.messages.SHOPPING_LIST_ERROR
                                )
                                return {"success": False, "action": "shopping_list_failed"}
                        except Exception as e:
                            logger.error(f"Ошибка при создании списка покупок: {str(e)}")
                            await self.send_message(
                                phone_number,
                                self.messages.SHOPPING_LIST_ERROR
                            )
                            return {"success": False, "action": "shopping_list_error"}

            # Команда для изменения плана питания (используем более широкий паттерн)
            update_diet_match = re.match(
                r'^(измени|поменяй|обнови|замени|скорректируй)\s+(план|меню|рацион|питание)(.*)$', message_text.lower())
            if update_diet_match:
                action = update_diet_match.group(1)  # измени/поменяй/и т.д.
                subject = update_diet_match.group(2)  # план/меню/и т.д.
                details = update_diet_match.group(3).strip()  # дополнительные детали запроса

                # Проверяем наличие активного плана
                diet_plan = await diet_service.get_current_diet(user_id)

                if not diet_plan:
                    # Пробуем еще раз найти план напрямую по user_id
                    plans = firebase_client.query_documents("diet_plans", "user_id", "==", user_id)
                    if plans:
                        # Берем самый недавний план
                        diet_plan = sorted(plans, key=lambda p: p.get("created_at", ""), reverse=True)[0]
                    else:
                        await self.send_message(
                            phone_number,
                            self.messages.NO_DIET_PLAN
                        )
                        return {"success": False, "action": "no_diet_plan_for_update"}

                # Сообщаем пользователю, что корректируем план
                await self.send_message(
                    phone_number,
                    self.messages.UPDATING_PLAN
                )

                try:
                    # Отправляем запрос к LLM-сервису для обновления диеты
                    updates = await llm_service.update_diet_plan(
                        diet_plan=diet_plan,
                        update_request=message_text
                    )

                    if "error" in updates:
                        logger.error(f"Ошибка при обновлении диеты: {updates['error']}")
                        await self.send_message(
                            phone_number,
                            "Извини, не удалось корректно обновить план питания. Попробуй запросить более конкретное изменение."
                        )
                        return {"success": False, "action": "diet_update_error", "error": updates.get("error")}

                    # Получаем комментарий
                    comment = updates.get("comment", "План питания обновлен согласно запросу")

                    # Обновляем план
                    success, updated_plan = await diet_service.update_diet_plan_partially(
                        diet_plan["id"],
                        updates["updated_days"],
                        comment
                    )

                    if success:
                        # Формируем сообщение об успешном обновлении
                        message = f"✅ *План питания обновлен*\n\n{comment}\n"

                        # Добавляем информацию об обновленных днях
                        for date_str in updates["updated_days"].keys():
                            try:
                                day_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                                day_name = translate_day_name(day_date.strftime("%A"))
                                message += f"\nОбновлено меню на *{day_name}, {day_date.strftime('%d.%m.%Y')}*"
                            except:
                                message += f"\nОбновлено меню на {date_str}"

                        # Отправляем сообщение пользователю
                        await self.send_message(phone_number, message)

                        # Получаем текущую дату
                        today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

                        # Отправляем детальный план на сегодня, если он был обновлен
                        if today.isoformat() in updates["updated_days"]:
                            day_plan = diet_service.get_day_diet_plan(updated_plan, today)
                            await self.send_message(phone_number, day_plan)

                        return {"success": True, "action": "diet_plan_updated"}
                    else:
                        await self.send_message(
                            phone_number,
                            "К сожалению, не удалось обновить план питания. Попробуй позже."
                        )
                        return {"success": False, "action": "update_failed"}

                except Exception as e:
                    logger.error(f"Ошибка при обновлении плана питания: {str(e)}")
                    await self.send_message(
                        phone_number,
                        "Извини, произошла ошибка при обновлении плана питания. Попробуй позже."
                    )
                    return {"success": False, "error": str(e)}

            # Обработка команд согласования плана
            # Находим последний несогласованный план
            pending_plans = firebase_client.query_documents(
                "diet_plans",
                "user_id", "==", user_id
            )
            # Фильтруем и находим последний план со статусом pending
            pending_plans = [p for p in pending_plans if p.get("status") == "pending"]

            if pending_plans:
                # Берем самый последний план
                last_pending_plan = max(pending_plans, key=lambda p: p.get("created_at", ""))
                # Обработка подтверждения которкого плана
                if message_text.lower() in ["согласен", "согласна", "подтверждаю", "ок", "да", "хорошо", "все ок"]:

                    # Согласуем план
                    success = await diet_service.approve_short_diet_plan(last_pending_plan["id"])

                    if success:
                        await self.send_message(
                            phone_number,
                            "✅ Отлично! Я начинаю готовить для вас полную версию плана питания с подробными рецептами и списком покупок. Это займет несколько минут."
                        )

                        # Запускаем генерацию полного плана
                        asyncio.create_task(self._generate_full_diet_plan(user_id, last_pending_plan["id"]))

                        return {"success": True, "action": "plan_approved"}
                    else:
                        await self.send_message(
                            phone_number,
                            "Извините, произошла ошибка при согласовании плана. Попробуйте позже."
                        )
                        return {"success": False, "action": "approval_failed"}

                # Команда для отклонения плана или запроса изменений краткого плана
                elif any(keyword in message_text.lower() for keyword in
                         ["измени", "поменяй", "замени", "не хочу", "не нравится", "добавь"]):

                    # Обрабатываем запрос на изменение
                    # Отправляем сообщение в LLM с запросом на изменение
                    update_result = await llm_service.update_short_diet_plan(
                        diet_plan=last_pending_plan,
                        update_request=message_text
                    )

                    if "error" in update_result:
                        await self.send_message(
                            phone_number,
                            "Извините, не удалось обработать ваш запрос на изменение плана. Пожалуйста, попробуйте более конкретное указание, например: 'Замени обед в понедельник на курицу'."
                        )
                        return {"success": False, "action": "update_error"}

                    if "updated_days" in update_result and update_result["updated_days"]:
                        # Обновляем план в базе данных
                        # TODO Доработать обновление отдельно для кратких планов тут используется для обновлении полных планов
                        success, updated_plan = await diet_service.update_short_diet_plan(
                            last_pending_plan["id"],
                            update_result["updated_days"],
                            update_result.get("comment", "Изменения внесены по запросу пользователя")
                        )

                        if success:
                            # Отправляем подтверждение изменений
                            confirmation = f"✅ План питания обновлен согласно вашему запросу.\n\n"

                            if "comment" in update_result:
                                confirmation += f"{update_result['comment']}\n\n"

                            confirmation += "Пожалуйста, оцените обновленный план и напишите 'согласен', если вас всё устраивает."

                            await self.send_message(phone_number, confirmation)

                            # Отправляем обновленную сводку плана
                            summary = diet_service.get_short_diet_summary(updated_plan)
                            await self.send_message(phone_number, summary)

                            return {"success": True, "action": "plan_updated"}
                        else:
                            await self.send_message(
                                phone_number,
                                "Извините, произошла ошибка при обновлении плана. Попробуйте позже."
                            )
                            return {"success": False, "action": "update_failed"}
                    else:
                        await self.send_message(
                            phone_number,
                            "Извините, не удалось внести изменения в план. Пожалуйста, попробуйте более конкретное указание, например: 'Замени обед в понедельник на курицу'."
                        )
                        return {"success": False, "action": "no_updates"}

            # Команда для отметки купленных продуктов
            bought_match = re.match(r'^купил[а]?\s+(.+)$', message_text.lower())
            if bought_match:
                product_name = bought_match.group(1).strip()

                # Получаем текущий план диеты
                diet_plan = await diet_service.get_current_diet(user_id)

                if not diet_plan:
                    await self.send_message(
                        phone_number,
                        "У тебя пока нет активного плана питания. Напиши 'диета' для создания нового плана."
                    )
                    return {"success": False, "action": "no_diet_plan"}

                # Получаем список покупок для текущего плана
                shopping_lists = firebase_client.query_documents(
                    "shopping_lists",
                    "diet_plan_id",
                    "==",
                    diet_plan["id"]
                )

                if not shopping_lists:
                    await self.send_message(
                        phone_number,
                        "Для твоего плана ещё не создан список покупок. Напиши 'список покупок' для его создания."
                    )
                    return {"success": False, "action": "no_shopping_list"}

                # Берем последний список покупок
                shopping_list = shopping_lists[0]

                # Найдем продукт в списке (нечеткий поиск)
                found = False
                updated_items = []

                for item in shopping_list.get("items", []):
                    item_name = item.get("name", "").lower()
                    if product_name.lower() in item_name or item_name in product_name.lower():
                        # Отмечаем продукт как купленный
                        item["is_purchased"] = True
                        found = True

                    updated_items.append(item)

                if found:
                    # Обновляем список покупок
                    firebase_client.update_document(
                        "shopping_lists",
                        shopping_list["id"],
                        {
                            "items": updated_items,
                            "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
                        }
                    )

                    await self.send_message(
                        phone_number,
                        f"✅ Отлично! Я отметил '{product_name}' как купленный."
                    )
                    return {"success": True, "action": "product_marked_as_purchased"}
                else:
                    await self.send_message(
                        phone_number,
                        f"Я не нашел '{product_name}' в твоем списке покупок. Проверь название продукта или напиши 'список покупок' для просмотра полного списка."
                    )
                    return {"success": False, "action": "product_not_found"}
            # Команда для генерации диеты
            if "диета" in message_text.lower():
                await self.start_short_diet_generation(phone_number, user_id)

                return {"success": True, "action": "short_diet_generation_started"}

            # Команда для получения статистики
            if "статистика" in message_text.lower() or "прогресс" in message_text.lower():
                try:
                    # Получаем прогресс по весу
                    weight_progress = await tracking_service.calculate_weight_progress(user_id)

                    # Получаем статус трекинга на сегодня
                    today_status = await tracking_service.get_daily_status(user_id)

                    # Получаем данные о соблюдении плана
                    today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()
                    compliance_data = await tracking_service.get_diet_compliance(user_id, today)

                    # Формируем сообщение статистики
                    message = f"*📊 СТАТИСТИКА И ПРОГРЕСС*\n\n"

                    # Прогресс по весу
                    if weight_progress:
                        message += f"*⚖️ Прогресс по весу:*\n"
                        message += f"• Начальный вес: {weight_progress.start_weight} кг\n"
                        message += f"• Текущий вес: {weight_progress.current_weight} кг\n"
                        message += f"• Целевой вес: {weight_progress.target_weight} кг\n\n"

                        if weight_progress.total_weight_change < 0:
                            message += f"• Изменение: -{abs(weight_progress.total_weight_change):.1f} кг 👍\n"
                        elif weight_progress.total_weight_change > 0:
                            message += f"• Изменение: +{weight_progress.total_weight_change:.1f} кг\n"
                        else:
                            message += "• Изменение: 0 кг (вес стабилен)\n"

                        message += f"• Осталось до цели: {abs(weight_progress.remaining_to_goal):.1f} кг\n"
                        message += f"• Процент выполнения: {weight_progress.goal_completion_percentage:.1f}%\n\n"

                    # Статус воды на сегодня
                    if today_status:
                        message += f"*💧 Потребление воды сегодня:*\n"
                        message += f"• Выпито: {today_status.current_water_intake} мл\n"
                        message += f"• Цель: {today_status.water_goal} мл\n"
                        message += f"• Выполнено: {today_status.water_percentage:.1f}%\n\n"

                    # Соблюдение плана питания
                    if compliance_data and "meals" in compliance_data and compliance_data["meals"]:
                        message += f"*🍽️ Соблюдение плана питания:*\n"

                        emoji_map = {
                            "followed": "✅",
                            "partially": "⚠️",
                            "substituted": "🔄",
                            "skipped": "❌",
                            "not_recorded": "❓"
                        }

                        for meal_type, status in compliance_data["meals"].items():
                            meal_type_ru = translate_meal_type(meal_type)
                            emoji = emoji_map.get(status, "❓")
                            message += f"• {meal_type_ru}: {emoji}\n"

                        if "overall_score" in compliance_data:
                            message += f"\nОбщее соблюдение: {compliance_data['overall_score']:.1f}%\n\n"

                    # Добавляем мотивационное сообщение
                    message += "💪 *Продолжай в том же духе!* Ты на пути к своей цели."

                    await self.send_message(phone_number, message)
                    return {"success": True, "action": "stats_sent"}
                except Exception as e:
                    logger.error(f"Ошибка при формировании статистики: {str(e)}")
                    await self.send_message(
                        phone_number,
                        "К сожалению, произошла ошибка при формировании статистики. Попробуйте позже."
                    )
                    return {"success": False, "action": "stats_error"}

            # Обработка обычного запроса с помощью LLM
            response = await llm_service.answer_nutrition_question(user_id, message_text)
            await self.send_message(phone_number, response)

            return {"success": True, "action": "ai_response_sent"}

        except Exception as e:
            self._log_error_with_context("Ошибка при обработке обычного сообщения", e, {
                "user_id": user.get("id", "unknown"),
                "phone_number": user.get("phone_number", "unknown"),
                "message_text": message_text,
                "message_type": message_type
            })
            return {"success": False, "error": str(e)}

    async def start_short_diet_generation(self, phone_number, user_id):
        await self.send_message(
            phone_number, self.messages.PLAN_GENERATION_STARTED
        )
        await self.send_message(
            phone_number,
            "После того, как я покажу вам план, вы сможете согласовать его или запросить изменения. После согласования я подготовлю полную версию с подробными рецептами и списком покупок."
        )
        # Генерируем краткий план
        short_plan = await diet_service.generate_short_diet_plan(user_id)
        if short_plan and "error" not in short_plan:
            # Отправляем сводку плана для согласования
            summary = diet_service.get_short_diet_summary(short_plan)
            await self.send_message(phone_number, summary)

            # Отправляем инструкции по согласованию
            instructions = """
                    👆 Это краткая версия вашего персонализированного плана питания на неделю.

                    Пожалуйста, подтвердите план или запросите изменения:
                    • Напишите "согласен", "ок" или "да", чтобы подтвердить план
                    • Или укажите, что именно вы хотели бы изменить, например:
                      "Замени обед во вторник"
                      "Не хочу рыбу в понедельник"
                      "Больше белка в завтраках"

                    После вашего подтверждения я подготовлю полную версию плана с подробными рецептами и списком покупок!
                    """
            await self.send_message(phone_number, instructions)
        else:
            error_msg = short_plan.get("error",
                                       "Неизвестная ошибка") if short_plan else "Не удалось создать план диеты"
            logger.error(f"Error generating short diet plan: {error_msg}")

            await self.send_message(
                phone_number,
                "К сожалению, не удалось создать план диеты. Пожалуйста, попробуйте позже или обратитесь в поддержку."
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

    def _get_next_onboarding_step(self, current_step: str) -> str:
        """Возвращает следующий шаг онбординга"""
        try:
            current_index = self.ONBOARDING_STEPS.index(current_step)
            next_index = current_index + 1

            if next_index >= len(self.ONBOARDING_STEPS):
                return "complete"

            return self.ONBOARDING_STEPS[next_index]
        except ValueError:
            return "name"  # Если шаг не найден, начинаем с имени

    def _process_onboarding_step(self, step: str, message_text: str) -> Optional[Dict[str, Any]]:
        """
        Обрабатывает ответ пользователя на шаге онбординга

        Args:
            step: Текущий шаг
            message_text: Текст сообщения

        Returns:
            Optional[Dict[str, Any]]: Данные для обновления пользователя или None в случае ошибки
        """
        try:
            # Очищаем текст сообщения
            message_text = message_text.strip()

            if step == "name":
                # Валидация имени
                if len(message_text) < 2 or len(message_text) > 50:
                    return None
                return {"name": message_text}

            elif step == "age":
                # Валидация возраста
                try:
                    age = int(message_text)
                    if age < 18 or age > 100:
                        return None
                    return {"age": age}
                except ValueError:
                    return None

            elif step == "gender":
                # Валидация пола
                gender_text = message_text.lower()
                if "муж" in gender_text:
                    return {"gender": "male"}
                elif "жен" in gender_text:
                    return {"gender": "female"}
                else:
                    return {"gender": "other"}

            elif step == "height":
                # Валидация роста
                try:
                    height = float(message_text.replace(',', '.'))
                    if height < 100 or height > 250:
                        return None
                    return {"height": height}
                except ValueError:
                    return None

            elif step == "current_weight":
                # Валидация текущего веса
                try:
                    weight = float(message_text.replace(',', '.'))
                    if weight < 30 or weight > 300:
                        return None
                    return {"current_weight": weight}
                except ValueError:
                    return None

            elif step == "target_weight":
                # Валидация целевого веса
                try:
                    weight = float(message_text.replace(',', '.'))
                    if weight < 30 or weight > 300:
                        return None
                    return {"target_weight": weight}
                except ValueError:
                    return None

            elif step == "activity_level":
                # Валидация уровня активности
                activity_text = message_text.lower()

                if "сид" in activity_text or "низк" in activity_text or "1" in activity_text:
                    return {"activity_level": "sedentary"}
                elif "легк" in activity_text or "2" in activity_text:
                    return {"activity_level": "light"}
                elif "сред" in activity_text or "умер" in activity_text or "3" in activity_text:
                    return {"activity_level": "moderate"}
                elif "высок" in activity_text or "4" in activity_text:
                    return {"activity_level": "high"}
                elif "очень высок" in activity_text or "спорт" in activity_text or "5" in activity_text:
                    return {"activity_level": "very_high"}
                else:
                    return {"activity_level": "moderate"}  # По умолчанию

            elif step == "weight_goal":
                # Валидация цели по весу
                goal_text = message_text.lower()

                if "похуд" in goal_text or "сниж" in goal_text or "1" in goal_text:
                    return {"weight_goal": "lose"}
                elif "поддерж" in goal_text or "сохран" in goal_text or "2" in goal_text:
                    return {"weight_goal": "maintain"}
                elif "набр" in goal_text or "увел" in goal_text or "3" in goal_text:
                    return {"weight_goal": "gain"}
                else:
                    return {"weight_goal": "lose"}  # По умолчанию для сервиса похудения

            elif step == "diet_preference":
                # Валидация предпочтений в диете
                pref_text = message_text.lower()

                if "обыч" in pref_text or "1" in pref_text:
                    return {"diet_preference": "regular"}
                elif "вегетар" in pref_text or "2" in pref_text:
                    return {"diet_preference": "vegetarian"}
                elif "веган" in pref_text or "3" in pref_text:
                    return {"diet_preference": "vegan"}
                elif "низкоуглевод" in pref_text or "4" in pref_text:
                    return {"diet_preference": "low_carb"}
                elif "кето" in pref_text or "5" in pref_text:
                    return {"diet_preference": "keto"}
                elif "безглютен" in pref_text or "6" in pref_text:
                    return {"diet_preference": "gluten_free"}
                else:
                    return {"diet_preference": "regular"}  # По умолчанию

            elif step == "allergies":
                # Обработка аллергий
                if message_text.lower() in ["нет", "не имею", "отсутствуют", "no"]:
                    return {"allergies": []}

                allergies = [a.strip() for a in message_text.split(',')]
                return {"allergies": allergies}

            elif step == "disliked_products":
                # Обработка нелюбимых продуктов
                if message_text.lower() in ["нет", "не имею", "отсутствуют", "no"]:
                    return {"disliked_products": []}

                disliked = [p.strip() for p in message_text.split(',')]
                return {"disliked_products": disliked}

            elif step == "budget":
                # Валидация бюджета
                try:
                    # Проверяем на ключевые слова неограниченного бюджета
                    message_lower = message_text.lower()
                    unlimited_keywords = [
                        "нет", "неограничен", "без ограничений", "без учета", "не важно",
                        "любой", "не имеет значения", "без бюджета", "неограниченный",
                        "no limit", "unlimited"
                    ]

                    # Проверка на ключевые слова
                    if any(keyword in message_lower for keyword in unlimited_keywords):
                        logger.info(f"Распознан неограниченный бюджет: '{message_text}'")
                        # Устанавливаем очень высокое значение и флаг неограниченного бюджета
                        return {"budget_limit": 10000, "budget_unlimited": True}

                    # Если нет ключевых слов, пробуем преобразовать в число
                    budget = float(message_text.replace(',', '.'))
                    if budget < 0:
                        return None
                    return {"budget_limit": budget, "budget_unlimited": False}
                except ValueError:
                    # Более информативное сообщение об ошибке в логах
                    logger.warning(f"Не удалось распознать бюджет: '{message_text}'")
                    return None

            # Если шаг не распознан
            return {}

        except Exception as e:
            logger.error(f"Ошибка при обработке шага онбординга {step}: {str(e)}")
            return None

    def _get_onboarding_step_message(self, step: str) -> str:
        """Возвращает понятное сообщение для шага онбординга с примерами"""

        examples = {
            "name": "Например: Мария",
            "age": "Например: 30",
            "gender": "Например: женский",
            "height": "Например: 165",
            "current_weight": "Например: 70",
            "target_weight": "Например: 65",
            "activity_level": "Например: 2 или 'умеренная'",
            "weight_goal": "Например: 1 или 'похудеть'",
            "diet_preference": "Например: 1 или 'обычная'",
            "allergies": "Например: орехи, молоко или 'нет'",
            "disliked_products": "Например: лук, свекла или 'нет'",
            "budget": "Например: 500 или 'неограничен'"
        }

        messages = {
            "name": "Как тебя зовут?",
            "age": "Сколько тебе лет?",
            "gender": "Укажи свой пол (мужской/женский/другой):",
            "height": "Какой у тебя рост в сантиметрах?",
            "current_weight": "Какой у тебя текущий вес в килограммах?",
            "target_weight": "Какой вес ты хочешь достичь (в килограммах)?",
            "activity_level": """Оцени свой уровень физической активности:
1. Сидячий образ жизни (мало или совсем нет физических нагрузок)
2. Легкая активность (легкие упражнения 1-3 раза в неделю)
3. Умеренная активность (умеренные упражнения 3-5 раз в неделю)
4. Высокая активность (интенсивные тренировки 6-7 раз в неделю)
5. Очень высокая активность (физическая работа или 2 тренировки в день)

Ответь номером или напиши своими словами:""",
            "weight_goal": """Какая у тебя цель по весу?
1. Похудеть
2. Поддерживать текущий вес
3. Набрать вес

Ответь номером или напиши своими словами:""",
            "diet_preference": """Какие у тебя предпочтения в питании?
1. Обычная диета (без ограничений)
2. Вегетарианская (без мяса, но с яйцами и молочными продуктами)
3. Веганская (только растительная пища)
4. Низкоуглеводная (ограничение углеводов)
5. Кето (высокое содержание жиров, очень низкое содержание углеводов)
6. Безглютеновая (без пшеницы, ржи и ячменя)

Ответь номером или напиши своими словами:""",
            "allergies": "Есть ли у тебя пищевые аллергии? Перечисли через запятую или напиши 'нет':",
            "disliked_products": "Есть ли продукты, которые ты не любишь или не хочешь включать в диету? Перечисли через запятую или напиши 'нет':",
            "budget": "Какой у тебя недельный бюджет на продукты питания (в кетцалях)? Если бюджет не ограничен, напиши 'неограничен':"
        }

        # Добавляем примеры к сообщению
        message = messages.get(step, "Пожалуйста, ответь на вопрос:")
        if step in examples:
            message += f"\n{examples[step]}"

        return message

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
