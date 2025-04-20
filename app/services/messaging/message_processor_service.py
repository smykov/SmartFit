import logging
import re
from datetime import datetime
from enum import Enum
from time import sleep
from typing import Dict, Any, Optional, Tuple

import pytz
from app.db.interfaces.message_repository_interface import IMessageRepository
from app.services.diet.diet_service_interface import IDietService
from app.services.localization.localization_interface import ILocalizationService
from app.constants.localization_keys import LocalizationKeys as LK
from app.services.onboarding.onboarding_service_interface import IOnboardingService
from app.services.tracking.tracking_service_interface import ITrackingService

from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.commands.command_factory import CommandFactory
from app.services.messaging.message_interface import IMessageService
from config import settings


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
    Сервис для обработки входящих сообщений, определения их типа и делегирования обработки
    соответствующим компонентам системы.
    """

    def __init__(
            self,
            user_repository: IUserRepository,
            message_repository: IMessageRepository,
            message_service: IMessageService,
            onboarding_service: IOnboardingService,
            diet_service: IDietService,
            tracking_service: ITrackingService,
            command_factory: CommandFactory,
            localization_service: ILocalizationService
    ):
        """
        Инициализация сервиса обработки сообщений

    Args:
        user_repository: Репозиторий для работы с пользователями
        message_repository: Репозиторий для работы с сообщениями
        message_service: Сервис для отправки сообщений
        onboarding_service: Сервис онбординга
        diet_service: Сервис для работы с диетами
        tracking_service: Сервис для трекинга прогресса
        command_factory: Фабрика команд для обработки команд пользователя
        localization_service: Сервис локализации для сообщений
        """
        self.user_repository = user_repository
        self.message_repository = message_repository
        self.message_service = message_service
        self.localization_service = localization_service
        self.onboarding_service = onboarding_service
        self.diet_service = diet_service
        self.tracking_service = tracking_service
        self.command_factory = command_factory
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
            # "product_bought": re.compile(r'^купил[а]?\s+(.+)$', re.IGNORECASE),
            "stats": re.compile(r'^(статистика|прогресс)$', re.IGNORECASE),
            "meal_compliance": re.compile(r'^(выполнено|частично|заменил[а]?|пропустил[а]?)\s+(\w+)$', re.IGNORECASE),
            "diet_update": re.compile(r'^(измени|поменяй|обнови|замени|скорректируй)\s+(план|меню|рацион|питание)(.*)$',
                                      re.IGNORECASE),
        }

        # Ответы на согласование плана
        self.approval_patterns = {
            "approve": re.compile(r'^(согласен|согласна|подтверждаю|ок|да|хорошо|все ок)$', re.IGNORECASE),
            "disapprove": re.compile(r'^(не согласен|не согласна|не подтверждаю|нет|не ок|не хорошо)$', re.IGNORECASE),
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

    async def process_incoming_message(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает входящее сообщение из WhatsApp

        Args:
            body: Данные входящего сообщения

        Returns:
            Dict[str, Any]: Результат обработки
        """
        try:
            # Извлекаем данные сообщения
            phone_number, message_text, message_type, message_id = self._extract_message_data(body)

            if not phone_number or not message_text:
                self.logger.error("Не удалось извлечь номер телефона или текст сообщения")
                return {"success": False, "error": self.get_localized_message(LK.Messaging.INVALID_MESSAGE_FORMAT)}

            # Проверяем, обрабатывалось ли это сообщение ранее
            if await self._is_message_processed(message_id):
                self.logger.info(f"Сообщение {message_id} уже обработано")
                return {"success": True, "action": "already_processed"}

            # Получаем пользователя по номеру телефона
            user = await self.user_repository.get_by_phone(phone_number)

            # Например, заменяем в блоке if not user:
            if not user:
                self.logger.info(f"Новый пользователь с номером {phone_number}. Начинаем регистрацию.")
                # Отправляем приветственное сообщение
                result = await self.onboarding_service.start_registration(phone_number)
                await self._mark_message_as_processed(message_id, phone_number, message_text)
                if result['success'] and result['user_id']:
                    user_id = result['user_id']
                    # Определение языка пользователя
                    if await self.localization_service.set_user_language(user_id, "en"):
                        # Отправляем приветственное сообщение
                        await self.message_service.send_template_message(phone_number, LK.Onboarding.WELCOME, user_id)
                    # Продолжаем онбординг
                    await self.onboarding_service.continue_onboarding(user_id, message_text)
                return result

            # Обновляем время последнего взаимодействия
            await self.user_repository.update(user["id"], {
                "last_interaction": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            })

            # Определяем стратегию обработки сообщения
            strategy = await self._determine_processing_strategy(user, message_text)
            self.logger.info(f"Выбрана стратегия обработки: {strategy} для пользователя {phone_number}")

            # Обрабатываем сообщение в соответствии с выбранной стратегией
            result = await self._process_with_strategy(strategy, user, message_text, message_type)

            # Отмечаем сообщение как обработанное
            await self._mark_message_as_processed(message_id, phone_number, message_text)

            return result

        except Exception as e:
            self.logger.error(f"Error processing incoming message: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _determine_processing_strategy(self, user: Dict[str, Any], message_text: str) -> ProcessingStrategy:
        """
        Определяет стратегию обработки сообщения на основе контекста пользователя и содержания сообщения

        Args:
            user: Данные пользователя
            message_text: Текст сообщения

        Returns:
            ProcessingStrategy: Стратегия обработки
        """
        # Если пользователь в процессе онбординга
        if not user.get("is_onboarding_completed", False):
            return ProcessingStrategy.ONBOARDING

        # Проверяем наличие ожидающего согласования плана диеты
        if await self._has_pending_diet_plan(user["id"]):
            # Если сообщение похоже на ответ о согласовании
            for pattern_name in ["approve", "disapprove"]:
                if self.approval_patterns[pattern_name].match(message_text):
                    return ProcessingStrategy.DIET_APPROVAL

            # Если сообщение похоже на запрос изменений в плане
            if self.command_patterns["diet_update"].match(message_text):
                return ProcessingStrategy.DIET_UPDATE

        # Проверяем является ли сообщение командой
        for pattern_name, pattern in self.command_patterns.items():
            if pattern.match(message_text):
                return ProcessingStrategy.COMMAND

        # Проверяем является ли сообщение трекингом данных
        if self._is_tracking_data(message_text):
            return ProcessingStrategy.TRACKING

        # По умолчанию считаем, что это запрос для ИИ
        return ProcessingStrategy.AI_RESPONSE

    async def _process_with_strategy(
            self,
            strategy: ProcessingStrategy,
            user: Dict[str, Any],
            message_text: str,
            message_type: str
    ) -> Dict[str, Any]:
        """
        Обрабатывает сообщение в соответствии с выбранной стратегией

        Args:
            strategy: Стратегия обработки
            user: Данные пользователя
            message_text: Текст сообщения
            message_type: Тип сообщения

        Returns:
            Dict[str, Any]: Результат обработки
        """
        if strategy == ProcessingStrategy.ONBOARDING:
            return await self.onboarding_service.continue_onboarding(user.get('id'), message_text)

        elif strategy == ProcessingStrategy.COMMAND:
            return await self._process_command(user, message_text)

        elif strategy == ProcessingStrategy.DIET_APPROVAL:
            return await self._process_diet_approval(user, message_text)

        elif strategy == ProcessingStrategy.DIET_UPDATE:
            return await self._process_diet_update(user, message_text)

        elif strategy == ProcessingStrategy.TRACKING:
            return await self._process_tracking_data(user, message_text)

        else:  # ProcessingStrategy.AI_RESPONSE
            return await self._process_ai_response(user, message_text)

    async def _process_command(self, user: Dict[str, Any], message_text: str) -> Dict[str, Any]:
        """
        Обрабатывает команду пользователя

        Args:
            user: Данные пользователя
            message_text: Текст сообщения с командой

        Returns:
            Dict[str, Any]: Результат обработки команды
        """

        diagnostic_info = self._diagnose_command_type(message_text)
        self.logger.debug(diagnostic_info)

        user_id = user["id"]
        phone_number = user["phone_number"]
        lang = await self.localization_service.get_user_language(user_id)

        # Определяем тип команды
        command_type = None
        command_params = {}

        for cmd_type, pattern in self.command_patterns.items():
            match = pattern.match(message_text)
            if match:
                command_type = cmd_type
                command_params = match.groupdict() if match.groupdict() else {}
                if match.groups():
                    command_params["params"] = match.groups()
                break

        if not command_type:
            self.logger.warning(f"Не удалось определить тип команды: {message_text}")
            await self.message_service.send_message(
                phone_number,
                self.get_localized_message(LK.Commands.General.COMMAND_NOT_FOUND, lang)
            )
            return {"success": False, "error": self.get_localized_message(LK.MessageProcessor.UNKNOWN_COMMAND, lang, message_text=message_text)}

        # Создаем команду через фабрику
        command = self.command_factory.create_command(command_type)

        # Проверяем, удалось ли создать команду
        if command is None:
            self.logger.error(f"Не удалось создать команду типа: {command_type}")
            await self.message_service.send_message(
                phone_number,
                self.get_localized_message(LK.MessageProcessor.COMMAND_NOT_FOUND, lang)
            )
            return {"success": False, "error": self.get_localized_message(LK.MessageProcessor.COMMAND_NOT_FOUND, lang)}

        # Проверяем предварительные условия
        if not await command.can_execute(user_id):
            # Сообщение о невозможности выполнить команду
            error_message = command.get_error_message()
            await self.message_service.send_message(phone_number, error_message)
            return {"success": False, "error": self.get_localized_message(LK.MessageProcessor.PREREQUISITES_NOT_MET, lang)}

        # Выполняем команду
        result = await command.execute(user_id, command_params)

        # Отправляем ответное сообщение, если команда это предусматривает
        if "message" in result and result["message"]:
            await self.message_service.send_message(phone_number, result["message"])

        # Отправляем ответные сообщения, если команда это предусматривает
        if "messages" in result and result["messages"]:
            for message in result["messages"]:
                await self.message_service.send_message(phone_number, message)

        return result

    def _diagnose_command_type(self, message_text: str) -> str:
        """
        Диагностический метод для определения типа команды

        Args:
            message_text: Текст сообщения

        Returns:
            str: Диагностическая информация
        """
        matches = []

        for cmd_type, pattern in self.command_patterns.items():
            match = pattern.match(message_text)
            if match:
                groups = match.groups() if match.groups() else []
                matches.append(f"Найдено соответствие для команды '{cmd_type}', группы: {groups}")

        if matches:
            return "Диагностика команды:\n" + "\n".join(matches)
        else:
            return f"Не найдено соответствие ни для одной команды: '{message_text}'"

    async def _process_diet_approval(self, user: Dict[str, Any], message_text: str) -> Dict[str, Any]:
        """
        Обрабатывает ответ на согласование плана питания

        Args:
            user: Данные пользователя
            message_text: Текст сообщения с ответом

        Returns:
            Dict[str, Any]: Результат обработки
        """
        user_id = user["id"]
        phone_number = user["phone_number"]
        lang = await self.localization_service.get_user_language(user_id)

        # Находим последний несогласованный план
        pending_plan = await self._get_pending_diet_plan(user_id)

        if not pending_plan:
            # Используем локализованное сообщение
            await self.message_service.send_message(
                phone_number,
                self.get_localized_message(LK.MessageProcessor.NO_PENDING_PLAN, lang)
            )
            return {"success": False, "action": "no_pending_plan"}

        # Определяем тип ответа (согласие или отказ)
        is_approved = bool(self.approval_patterns["approve"].match(message_text))

        if is_approved:
            # Согласуем план
            success = await self.diet_service.approve_short_diet_plan(pending_plan["id"])

            if success:
                await self.message_service.send_template_message(
                    phone_number,
                    "diet.short.approval_success",
                    user_id
                )

                # Запускаем генерацию полного плана
                await self.diet_service.start_full_diet_generation(user_id, pending_plan["id"])

                return {"success": True, "action": "plan_approved"}
            else:
                await self.message_service.send_template_message(
                    phone_number,
                    "diet.approval_error",
                    user_id
                )
                return {"success": False, "action": "approval_failed"}
        else:
            # Отклонение плана
            await self.message_service.send_template_message(
                phone_number,
                "diet.disapproval",
                user_id
            )
            return {"success": True, "action": "plan_disapproved"}

    async def _process_diet_update(self, user: Dict[str, Any], message_text: str) -> Dict[str, Any]:
        """
        Обрабатывает запрос на обновление плана питания

        Args:
            user: Данные пользователя
            message_text: Текст сообщения с запросом на обновление

        Returns:
            Dict[str, Any]: Результат обработки
        """
        today = datetime.now(pytz.timezone(settings.TIMEZONE))
        user_id = user["id"]
        phone_number = user["phone_number"]
        lang = await self.localization_service.get_user_language(user_id)

        # Проверяем наличие активного плана
        diet_plan = await self.diet_service.get_current_diet(user_id)

        if not diet_plan:
            await self.message_service.send_message(
                phone_number,
                self.get_localized_message(LK.MessageProcessor.NO_DIET_PLAN, lang)
            )
            return {"success": False, "action": "no_diet_plan_for_update"}

        # Сообщаем пользователю, что корректируем план
        await self.message_service.send_message(
            phone_number,
            self.get_localized_message(LK.MessageProcessor.UPDATING_PLAN, lang)
        )

        # Проверяем, нужно ли обновлять краткий или полный план
        if diet_plan.get("version") == "short" and diet_plan.get("status") == "pending":
            result = await self.diet_service.update_short_diet_plan_by_request(
                diet_plan["id"],
                message_text
            )
        else:
            result = await self.diet_service.update_diet_plan(
                diet_plan["id"],
                message_text
            )

        if "error" in result:
            await self.message_service.send_message(
                phone_number,
                self.get_localized_message(LK.MessageProcessor.UPDATE_FAILED, lang)
            )
            return {"success": False, "action": "diet_update_error", "error": result.get("error")}

        # Формируем и отправляем сообщение о результате обновления
        if "success" in result and result["success"]:
            update_message = self.get_localized_message(
                LK.Diet.Update.SUCCESS_HEADER,
                lang,
                comment=result.get("comment", "")
            )
            await self.message_service.send_message(phone_number, update_message)

            # Если был обновлен план на сегодня, отправляем его
            if self._is_today_updated(result.get("updated_days", {})):
                today_plan = self.diet_service.get_day_diet_plan(result["plan"], today, lang)
                if today_plan:
                    await self.message_service.send_messages(phone_number, today_plan)

            return {"success": True, "action": "diet_plan_updated"}
        else:
            await self.message_service.send_message(
                phone_number,
                self.get_localized_message(LK.MessageProcessor.UPDATE_FAILED, lang)
            )
            return {"success": False, "action": "update_failed"}

    async def _process_tracking_data(self, user: Dict[str, Any], message_text: str) -> Dict[str, Any]:
        """
        Обрабатывает данные для трекинга

        Args:
            user: Данные пользователя
            message_text: Текст сообщения с данными для трекинга

        Returns:
            Dict[str, Any]: Результат обработки
        """
        # Логика обработки данных трекинга должна быть реализована
        # TODO дописать обработку трекинга
        # в соответствующем сервисе трекинга
        return {"success": False, "action": "not_implemented"}

    async def _process_ai_response(self, user: Dict[str, Any], message_text: str) -> Dict[str, Any]:
        """
        Обрабатывает обычный запрос, требующий ответа ИИ

        Args:
            user: Данные пользователя
            message_text: Текст запроса

        Returns:
            Dict[str, Any]: Результат обработки
        """
        user_id = user["id"]
        phone_number = user["phone_number"]

        # Получаем ответ от ИИ через сервис диет
        response = await self.diet_service.answer_nutrition_question(user_id, message_text, user["language"])

        context = {
            "message_type": "ai_response",
            "user_id": user_id
        }

        # Отправляем ответ пользователю
        await self.message_service.send_message(phone_number, response, context)

        return {"success": True, "action": "ai_response_sent"}

    def _extract_message_data(self, body: Dict[str, Any]) -> Tuple[
        Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Извлекает данные из входящего сообщения WhatsApp

        Args:
            body: Данные сообщения

        Returns:
            Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
            (номер телефона, текст сообщения, тип сообщения, ID сообщения)
        """
        try:
            phone_number = body.get("From", "").replace("whatsapp:", "")
            message_text = body.get("Body", "")
            message_type = MessageType.TEXT  # По умолчанию текстовое сообщение
            message_id = body.get("MessageSid", "") or body.get("SmsMessageSid", "")

            # Проверяем, есть ли медиа в сообщении
            if "MediaUrl0" in body:
                message_type = MessageType.MEDIA

            return phone_number, message_text, message_type, message_id

        except Exception as e:
            self.logger.error(f"Error when extracting message data: {str(e)}")
            return None, None, None, None

    async def _is_message_processed(self, message_id: str) -> bool:
        """
        Проверяет, было ли сообщение уже обработано

        Args:
            message_id: ID сообщения

        Returns:
            bool: True, если сообщение уже обработано
        """
        return await self.message_repository.is_processed(message_id)

    async def _mark_message_as_processed(self, message_id: str, phone_number: str, message_text: str) -> None:
        """
        Отмечает сообщение как обработанное

        Args:
            message_id: ID сообщения
            phone_number: Номер телефона отправителя
            message_text: Текст сообщения
        """
        await self.message_repository.mark_as_processed(
            message_id,
            phone_number,
            message_text,
            datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
        )

    def _is_tracking_data(self, message_text: str) -> bool:
        """
        Проверяет, является ли сообщение данными для трекинга

        Args:
            message_text: Текст сообщения

        Returns:
            bool: True, если сообщение содержит данные для трекинга
        """
        # Реализация логики определения данных трекинга
        # Пока заглушка
        return False

    async def _has_pending_diet_plan(self, user_id: str) -> bool:
        """
        Проверяет, есть ли у пользователя несогласованный план питания

        Args:
            user_id: ID пользователя

        Returns:
            bool: True, если есть несогласованный план
        """
        plan = await self._get_pending_diet_plan(user_id)
        return bool(plan)

    async def _get_pending_diet_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает несогласованный план питания пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: План питания или None
        """
        return await self.diet_service.get_pending_diet_plan(user_id)

    def _is_today_updated(self, updated_days: Dict[str, Any]) -> bool:
        """
        Проверяет, обновлен ли план на сегодня

        Args:
            updated_days: Словарь обновленных дней

        Returns:
            bool: True, если обновлен план на сегодня
        """
        today = datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat()
        return today in updated_days