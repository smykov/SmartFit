# app/services/messaging/message_processor_service.py
import logging
import re
from enum import Enum
from typing import Dict, Any, Optional

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.messaging.messenger_registry import MessengerRegistry
from app.services.user.user_identity_service import UserIdentityService
from app.db.interfaces.message_repository_interface import IMessageRepository
from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.onboarding.onboarding_service_interface import IOnboardingService
from app.services.localization.localization_interface import ILocalizationService
from app.services.commands.command_factory import CommandFactory
from app.services.messaging.interfaces.message_interface import IMessengerService
from app.services.tracking.tracking_service_interface import ITrackingService
from app.services.diet.diet_service_interface import IDietService
from app.services.messaging.command_extraction.command_extraction_interface import ICommandExtractor
from app.services.messaging.command_extraction.command_executor import CommandExecutor
from app.utils.date_helper import DateHelper


class MessageType(str, Enum):
    """Типы сообщений, поддерживаемые системой"""
    TEXT = "text"
    MEDIA = "media"
    LOCATION = "location"
    CONTACT = "contact"
    INTERACTIVE = "interactive"
    BUTTON = "button"
    TEMPLATE = "template"


class ProcessingStrategy(str, Enum):
    """Стратегии обработки сообщений"""
    ONBOARDING = "onboarding"  # Сообщение в процессе онбординга
    COMMAND = "command"  # Сообщение является командой
    DIET_APPROVAL = "diet_approval"  # Ответ на согласование плана питания
    DIET_UPDATE = "diet_update"  # Запрос на обновление плана питания
    TRACKING = "tracking"  # Запись данных для трекинга
    AI_RESPONSE = "ai_response"  # Обычный вопрос для ИИ-ответа


class MessageProcessorService:
    """
    Сервис для обработки входящих сообщений из разных мессенджеров
    Ответственность: Обработка и маршрутизация входящих сообщений
    """

    def __init__(
            self,
            messenger_registry: MessengerRegistry,
            user_identity_service: UserIdentityService,
            user_repository: IUserRepository,
            message_repository: IMessageRepository,
            messenger_service: IMessengerService,
            onboarding_service: IOnboardingService,
            diet_service: IDietService,
            tracking_service: ITrackingService,
            command_factory: CommandFactory,
            localization_service: ILocalizationService,
            command_extractor: ICommandExtractor,
            command_executor: CommandExecutor
    ):
        """
        Инициализация сервиса обработки сообщений

        Args:
            messenger_registry: Реестр мессенджеров
            user_identity_service: Сервис идентификации пользователей
            user_repository: Репозиторий для работы с пользователями
            message_repository: Репозиторий для работы с сообщениями
            messenger_service: Сервис отправки сообщений
            onboarding_service: Сервис онбординга
            diet_service: Сервис для работы с диетами
            tracking_service: Сервис для трекинга прогресса
            command_factory: Фабрика команд для обработки команд пользователя
            localization_service: Сервис локализации для сообщений
            command_extractor: Экстрактор команд из сообщений пользователя
            command_executor: Исполнитель команд
        """
        self.messenger_registry = messenger_registry
        self.user_identity_service = user_identity_service
        self.user_repository = user_repository
        self.onboarding_service = onboarding_service
        self.localization_service = localization_service
        self.message_repository = message_repository
        self.messenger_service = messenger_service
        self.diet_service = diet_service
        self.tracking_service = tracking_service
        self.command_factory = command_factory
        self.command_extractor = command_extractor
        self.command_executor = command_executor
        self.DEFAULT_LANGUAGE = self.localization_service.DEFAULT_LANGUAGE
        self.logger = logging.getLogger(self.__class__.__name__)

        # Регулярные выражения для определения типов сообщений
        self.command_patterns = {
            "weight": re.compile(r'^вес\s+(\d+[.,]?\d*)$', re.IGNORECASE),
            "water": re.compile(r'^вода\s+(\d+[.,]?\d*)$', re.IGNORECASE),
            "help": re.compile(r'^(помощь|справка|команды|help)$', re.IGNORECASE),
            "diet": re.compile(r'^(диета|план|план питания|меню)$', re.IGNORECASE),
            # "diet_today": re.compile(r'^(план|меню)\s+на\s+сегодня$', re.IGNORECASE),
            # "diet_tomorrow": re.compile(r'^(план|меню)\s+на\s+завтра$', re.IGNORECASE),
            # "diet_full": re.compile(r'^(полный план|полное меню)$', re.IGNORECASE),
            "shopping_list": re.compile(r'^список покупок$', re.IGNORECASE),
            "product_bought": re.compile(r'^купил[а]?\s+(.+)$', re.IGNORECASE),
            "stats": re.compile(r'^(статистика|прогресс)$', re.IGNORECASE),
            "meal_compliance": re.compile(r'^(выполнено|частично|заменил[а]?|пропустил[а]?|1|2|3|4)\s+(\w+)$',
                                          re.IGNORECASE),
            "diet_update": re.compile(r'^(измени|поменяй|обнови|замени|скорректируй)\s+(план|меню|рацион|питание)(.*)$',
                                      re.IGNORECASE),
        }

        # Ответы на согласование плана
        self.approval_patterns = {
            "approve": re.compile(r'^(согласен|согласна|подтверждаю|ок|да|хорошо|все ок|yes|ok)$', re.IGNORECASE),
            "disapprove": re.compile(r'^(не согласен|не согласна|не подтверждаю|нет|не ок|не хорошо|no|отклоняю)$',
                                     re.IGNORECASE),
        }

    def get_localized_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        """
        Получает локализованное сообщение из сервиса локализации

        Args:
            key: Ключ сообщения
            lang: Код языка (по умолчанию используется системный язык)
            **params: Параметры для форматирования

        Returns:
            str: Локализованное сообщение
        """
        if self.localization_service:
            return self.localization_service.get_message(key, lang, **params)
        return key

    async def process_incoming_message(self, data: Dict[str, Any],
                                       messenger_type: str) -> Dict[str, Any]:
        """
        Универсальный метод обработки входящих сообщений

        Args:
            data: Данные сообщения
            messenger_type: Тип мессенджера

        Returns:
            Dict[str, Any]: Результат обработки
        """
        try:
            # Получаем мессенджер из реестра
            messenger = self.messenger_registry.get_messenger(messenger_type)
            if not messenger:
                self.logger.error(f"Messenger '{messenger_type}' not found")
                return {"success": False, "error": self.get_localized_message(LK.Messaging.ERROR)}

            # Парсим данные сообщения через мессенджер
            parsed_message = await messenger.parse_incoming_message(data)
            if not parsed_message:
                self.logger.error("Failed to parse message")
                return {"success": False, "error": self.get_localized_message(LK.Messaging.ERROR)}

            # Извлекаем необходимые данные
            sender_id = parsed_message.get("sender_id")
            message_text = parsed_message.get("message_text")
            message_type = parsed_message.get("message_type", "text")
            message_id = parsed_message.get("message_id")
            lang = parsed_message.get("language_code", self.DEFAULT_LANGUAGE)
            # TODO брать из модуля локализации список языков
            if not lang or lang not in ["ru", "en", "es"]:
                lang = self.DEFAULT_LANGUAGE

            # Сразу отмечаем сообщение как "в обработке"
            if message_id:
                timestamp = DateHelper.get_current_datetime().isoformat()
                await self.message_repository.mark_as_processing(message_id, sender_id, message_text, timestamp)

            if not sender_id or not message_text:
                self.logger.error("Missing required message data")
                return {"success": False, "error": self.get_localized_message(LK.Messaging.INVALID_MESSAGE_FORMAT)}

            # Проверяем, обрабатывалось ли это сообщение ранее
            if await self.is_message_being_processed(message_id):
                self.logger.info(f"Сообщение {message_id} уже обработано")
                return {"success": True, "action": "already_processed"}

            # Получаем пользователя
            # Сначала ищем через сервис управления идентичностью
            user = await self.user_identity_service.get_user_by_messenger_id(messenger_type, sender_id)

            # Если пользователь не найден, начинаем регистрацию
            if not user:
                self.logger.info(f"New user from {messenger_type} with ID {sender_id}")
                return await self._handle_new_user(sender_id, message_text, message_id, messenger_type, lang)

            # Обновляем информацию о последнем взаимодействии
            await self.user_repository.update(user["id"], {
                "last_interaction": DateHelper.get_current_datetime().isoformat(),
                "last_interaction_messenger": messenger_type
            })

            # Если пользователь в процессе онбординга, передаем управление сервису онбординга
            if not user.get("is_onboarding_completed", False):
                self.logger.info(f"User {sender_id} is in onboarding process")
                result = await self.onboarding_service.continue_onboarding(user.get('id'), message_text)

                # Отмечаем сообщение как обработанное
                if message_id:
                    await self._mark_message_as_processed(message_id, sender_id, message_text)

                return result

            # Получаем контекст пользователя для извлечения команд
            user_context = await self._get_user_conversation_context(user["id"])

            # Дополняем контекст информацией о текущем состоянии
            context_with_state = await self._enrich_context_with_state(user_context, user["id"])

            # Извлекаем команды из сообщения пользователя
            extraction_result = await self.command_extractor.extract_commands(
                message_text,
                user["id"],
                context_with_state
            )

            # Логируем результат извлечения
            self.logger.info(f"Command extraction result: source={extraction_result.source}, "
                             f"commands={[cmd.command_type for cmd in extraction_result.commands]}, "
                             f"fallback_to_ai={extraction_result.fallback_to_ai}")

            # Сохраняем контекст разговора
            await self._store_user_conversation_context(user["id"], f"message_received", {
                "message_text": message_text,
                "message_type": message_type,
                "messenger_type": messenger_type,
                "commands": [cmd.dict() for cmd in extraction_result.commands],
                "fallback_to_ai": extraction_result.fallback_to_ai
            })

            # Если есть команды для выполнения и не требуется fallback, выполняем их
            if extraction_result.commands and extraction_result.execution_required and not extraction_result.fallback_to_ai:
                # Отправляем дополнительное текстовое сообщение, если оно есть
                if extraction_result.response_message:
                    await self.messenger_service.send_message(
                        sender_id,
                        extraction_result.response_message,
                        {"user_id": user["id"], "messenger_type": messenger_type}
                    )

                # Выполняем команды
                execution_result = await self.command_executor.execute_commands(
                    user["id"],
                    extraction_result.commands,
                    messenger_type,
                    extraction_result.response_message,
                    extraction_result.source
                )

                # Отмечаем сообщение как обработанное
                await self._mark_message_as_processed(message_id, sender_id, message_text)

                # Сохраняем результат выполнения в контекст
                await self._store_user_conversation_context(user["id"], "commands_executed", {
                    "message_text": message_text,
                    "message_type": message_type,
                    "messenger_type": messenger_type,
                    "commands": [cmd.dict() for cmd in extraction_result.commands],
                    "response_message": extraction_result.response_message
                })

                return {
                    "success": True,
                    "action": "commands_executed",
                    "execution_result": execution_result
                }

            # Если нужен fallback на AI или нет команд, используем общий AI-ответ
            if extraction_result.fallback_to_ai or not extraction_result.commands:
                # Получаем ответ от ИИ
                response = await self.diet_service.answer_nutrition_question(user["id"], message_text, lang)

                # Отправляем ответ пользователю
                await self.messenger_service.send_message(
                    sender_id,
                    response,
                    {"message_type": "ai_response", "user_id": user["id"], "messenger_type": messenger_type}
                )

                # Отмечаем сообщение как обработанное
                await self._mark_message_as_processed(message_id, sender_id, message_text)

                # Сохраняем результат в контекст
                await self._store_user_conversation_context(user["id"], "ai_response_sent", {
                    "query": message_text,
                    "response": response
                })

                return {
                    "success": True,
                    "action": "ai_response_sent"
                }

            # В случае неопределенной ситуации
            self.logger.warning(f"Unhandled message processing case for user {sender_id}")
            return {"success": False, "error": "Unhandled message processing case"}

        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _handle_new_user(self, sender_id: str, message_text: str, message_id: str,
                               messenger_type: str, lang: str) -> Dict[str, Any]:
        """Обработка сообщения от нового пользователя"""
        try:
            # Запускаем процесс регистрации
            result = await self.onboarding_service.start_registration(sender_id, messenger_type)

            # Отмечаем сообщение как обработанное
            await self._mark_message_as_processed(message_id, sender_id, message_text)

            if result['success'] and result['user_id']:
                user_id = result['user_id']

                # Явно устанавливаем язык при создании аккаунта
                await self.localization_service.set_user_language(user_id, lang)

                # Связываем ID мессенджера с пользователем
                await self.user_identity_service.link_messenger_account(
                    user_id, messenger_type, sender_id
                )

                # Отправляем приветственное сообщение
                context = {
                    "messenger_type": messenger_type,
                    "user_id": user_id
                }
                await self.messenger_service.send_template_message(
                    sender_id, LK.Onboarding.WELCOME, user_id, {}
                )

                # Продолжаем онбординг с полученным сообщением
                await self.onboarding_service.continue_onboarding(user_id, message_text)

            return result
        except Exception as e:
            self.logger.error(f"Ошибка при обработке нового пользователя: {str(e)}")
            return {"success": False, "error": str(e)}

    async def is_message_being_processed(self, message_id: str) -> bool:
        """
        Проверяет, находится ли сообщение в процессе обработки

        Args:
            message_id: ID сообщения

        Returns:
            bool: True, если сообщение уже обрабатывается
        """
        if not message_id:
            return False

        try:
            # Проверяем статус сообщения
            message_status = await self.message_repository.get_message_status(message_id)
            return message_status == "processed"
        except Exception as e:
            self.logger.error(f"Error checking message processing status: {str(e)}")
            return False

    async def _mark_message_as_processed(self, message_id: str, sender_id: str, message_text: str) -> None:
        """
        Отмечает сообщение как обработанное

        Args:
            message_id: ID сообщения
            sender_id: Номер отправителя
            message_text: Текст сообщения
        """
        # Проверяем валидность message_id
        if not message_id:
            self.logger.warning("Cannot mark message as processed: empty message_id")
            return

        try:
            # Используем await для асинхронного метода
            result = await self.message_repository.mark_as_processed(
                message_id,
                sender_id,
                message_text,
                DateHelper.get_current_datetime().isoformat()
            )

            if not result:
                self.logger.warning(f"Failed to mark message {message_id} as processed")
        except Exception as e:
            self.logger.error(f"Error marking message as processed: {str(e)}", exc_info=True)

    async def _get_user_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """
        Получает контекст разговора пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Dict[str, Any]: Контекст разговора
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user or "last_conversation_context" not in user:
            return {}

        return user.get("last_conversation_context", {})

    async def _store_user_conversation_context(self, user_id: str, action: str, data: Dict[str, Any] = None) -> None:
        """
        Сохраняет контекст разговора пользователя

        Args:
            user_id: ID пользователя
            action: Действие, которое было выполнено
            data: Дополнительные данные
        """
        context = {
            "last_action": action,
            "last_action_time": DateHelper.get_current_datetime().isoformat(),
            "last_message": data.get("message_text", "") if data else "",
            "data": data
        }

        # Сохраняем в репозитории пользователей
        await self.user_repository.update(user_id, {
            "last_conversation_context": context,
            "updated_at": DateHelper.get_current_datetime().isoformat()
        })

    async def _enrich_context_with_state(self, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Дополняет контекст информацией о текущем состоянии пользователя

        Args:
            context: Исходный контекст
            user_id: ID пользователя

        Returns:
            Dict[str, Any]: Дополненный контекст
        """
        enriched = context.copy() if context else {}

        try:
            # Получаем пользователя для определения часового пояса
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return enriched

            # Получаем трекинговую дату
            tracking_date = DateHelper.get_tracking_date(user.get("timezone"))

            # Проверяем наличие плана диеты
            current_diet = await self.diet_service.get_current_diet(user_id)
            if current_diet:
                enriched["has_diet_plan"] = True
                enriched["diet_plan_id"] = current_diet.get("id")

                # Добавляем информацию о днях плана питания
                if "daily_plans" in current_diet:
                    enriched["current_diet_days"] = list(current_diet["daily_plans"].keys())

                # Получаем план на сегодня для детального контекста
                today_plan = await self.diet_service.get_diet_for_day(user_id, tracking_date)
                if today_plan:
                    enriched["today_diet_plan"] = {
                        "date": tracking_date.isoformat(),
                        "day_of_week": DateHelper.get_day_of_week(tracking_date),
                        "meals": today_plan.get("meals", []),
                        "total_calories": today_plan.get("total_calories", 0),
                        "total_proteins": today_plan.get("total_proteins", 0),
                        "total_fats": today_plan.get("total_fats", 0),
                        "total_carbs": today_plan.get("total_carbs", 0)
                    }

            daily_tracking = await self.tracking_service.get_daily_tracking_history(user_id, tracking_date)
            if daily_tracking:
                enriched["daily_tracking_history"] = daily_tracking

                # Добавляем краткую сводку для удобства LLM
                enriched["tracking_summary"] = {
                    "completed_meals": [
                        meal_type for meal_type, meal_data in daily_tracking.get("meals_tracking", {}).items()
                        if meal_data.get("status") in ["followed", "partially", "substituted"]
                    ],
                    "skipped_meals": [
                        meal_type for meal_type, meal_data in daily_tracking.get("meals_tracking", {}).items()
                        if meal_data.get("status") == "skipped"
                    ],
                    "total_calories_consumed": daily_tracking.get("cumulative_nutrients", {}).get("calories", 0),
                    "total_proteins_consumed": daily_tracking.get("cumulative_nutrients", {}).get("proteins", 0),
                    "total_fats_consumed": daily_tracking.get("cumulative_nutrients", {}).get("fats", 0),
                    "total_carbs_consumed": daily_tracking.get("cumulative_nutrients", {}).get("carbs", 0),
                    "water_consumed": daily_tracking.get("daily_totals", {}).get("water_consumed", 0),
                    "compliance_score": daily_tracking.get("overall_compliance_score", 0)
                }

            # Получаем последние данные о весе
            weight_entries = await self.tracking_service.get_recent_weight_entries(user_id, 1)
            if weight_entries:
                enriched["latest_weight"] = weight_entries[0].get("weight")
                enriched["latest_weight_date"] = weight_entries[0].get("date")

            # Получаем последний план с ожиданием согласования
            pending_plan = await self.diet_service.get_pending_diet_plan(user_id)
            if pending_plan:
                enriched["has_pending_diet_plan"] = True
                enriched["pending_plan_id"] = pending_plan.get("id")

        except Exception as e:
            self.logger.error(f"Error enriching context with state: {str(e)}")

        return enriched
