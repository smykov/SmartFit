# app/services/reminders/reminder_service.py

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import pytz
from app.constants.localization_keys import LocalizationKeys as LK
from app.services.diet.diet_service_interface import IDietService
from app.services.tracking.tracking_service_interface import ITrackingService

from app.db.interfaces.reminder_repository_interface import IReminderRepository
from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.messaging.interfaces.message_interface import IMessengerService
from app.services.localization.localization_interface import ILocalizationService
from app.services.reminders.reminder_service_interface import IReminderService
from app.services.reminders.reminder_factory import ReminderFactory
from app.services.reminders.reminder_strategies import ReminderStrategy, PlanApprovalReminderStrategy
from app.utils.date_helper import DateHelper
from config import settings


class ReminderService(IReminderService):
    """
    Сервис для управления системой напоминаний пользователям

    Отвечает за:
    - Отправку напоминаний о незавершенном онбординге
    - Отправку напоминаний о трекинге веса, воды и приемов пищи
    - Отправку напоминаний о согласовании плана питания
    - Отправку еженедельных отчетов
    """

    def __init__(
            self,
            messenger_service: IMessengerService,
            user_repository: IUserRepository,
            reminder_repository: IReminderRepository,
            tracking_service: ITrackingService,
            diet_service: IDietService,
            localization_service: ILocalizationService,
    ):
        """
        Инициализация сервиса напоминаний

        Args:
            messenger_service: Сервис для отправки сообщений
            user_repository: Репозиторий для работы с пользователями
            reminder_repository: Репозиторий для работы с напоминаниями
            tracking_service: Сервис трекинга (опционально)
            diet_service: Сервис диет (опционально)
            localization_service: Сервис локализации (опционально)
        """
        self.messenger_service = messenger_service
        self.user_repository = user_repository
        self.reminder_repository = reminder_repository
        self.tracking_service = tracking_service
        self.diet_service = diet_service
        self.localization_service = localization_service
        self.logger = logging.getLogger(self.__class__.__name__)

        # Инициализация стратегий напоминаний
        self.reminder_strategies = ReminderFactory.create_all_strategies()

    def get_localized_message(self, key: str, lang: str = None, **params) -> str:
        """
        Получает локализованное сообщение из сервиса локализации

        Args:
            key: Ключ сообщения
            lang: Код языка (по умолчанию используется системный язык)
            **params: Параметры для форматирования

        Returns:
            str: Локализованное сообщение
        """
        if hasattr(self, 'localization_service') and self.localization_service:
            return self.localization_service.get_message(key, lang, **params)
        return key

    async def initialize(self):
        """Инициализация сервиса и запуск регулярных задач"""
        try:
            self.logger.info("Initializing reminder service...")

            # Запускаем периодические задачи для отправки напоминаний
            asyncio.create_task(self._run_reminder_tasks())

            self.logger.info("Reminder service initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing reminder service: {str(e)}")

    async def _run_reminder_tasks(self):
        """Запускает регулярные задачи для проверки и отправки напоминаний"""
        while True:
            try:
                # Создаем контекст времени
                context = self._create_time_context()

                # Пропускаем отправку напоминаний в ночное время
                if context["is_night"]:
                    await asyncio.sleep(1800)  # 30 минут
                    continue

                # Отправляем напоминания о незавершенном онбординге
                await self.send_onboarding_reminders()

                # Отправляем напоминания о согласовании плана
                await self.send_plan_approval_reminders()

                # Отправляем напоминания о трекинге в зависимости от времени суток
                await self.send_tracking_reminders(context)

                # Ждем 30 минут до следующей проверки
                await asyncio.sleep(1800)
            except asyncio.CancelledError:
                self.logger.info("Reminder tasks cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in reminder tasks: {str(e)}")
                await asyncio.sleep(300)  # 5 минут

    async def send_onboarding_reminders(self):
        """Отправляет напоминания пользователям с незавершенным онбордингом"""
        try:
            # Получаем пользователей с незавершенным онбордингом
            users = await self.user_repository.find_with_incomplete_onboarding()

            # Текущее время
            now = DateHelper.get_current_datetime()

            # Обрабатываем каждого пользователя
            for user in users:
                try:
                    user_id = user.get("id")
                    phone_number = user.get("phone_number")

                    if not phone_number:
                        continue

                    # Получаем язык пользователя
                    lang = await self.localization_service.get_user_language(user_id)

                    # Получаем информацию о последнем взаимодействии
                    last_interaction = None
                    if "last_interaction" in user:
                        try:
                            last_interaction = datetime.fromisoformat(user["last_interaction"])
                        except (ValueError, TypeError):
                            pass

                    # Если последнее взаимодействие было более 4 часов назад (или не было вообще)
                    if not last_interaction or (now - last_interaction).total_seconds() > 14400:  # 4 часа
                        current_step = user.get("onboarding_step", "welcome")

                        # Формируем сообщение-напоминание
                        reminder_message = self._get_onboarding_reminder(current_step, user.get("name", ""), lang)

                        # Получаем константы для типа напоминания
                        reminder_type = self.get_localized_message(LK.Reminders.REMINDER_TYPE_ONBOARDING, lang)

                        # Создаем контекст для напоминания
                        context = {
                            "onboarding_step": current_step,
                            "user_id": user_id
                        }

                        # Отправляем напоминание
                        if await self.can_send_reminder(phone_number, reminder_type, 86400):  # 24 часа
                            # Специальный случай для онбординга - сообщение уже сформировано
                            await self.messenger_service.send_message(
                                phone_number,
                                reminder_message,
                                context
                            )

                            # Записываем информацию об отправленном напоминании
                            await self.record_reminder_sent(phone_number, reminder_type)

                            self.logger.info(f"Sent onboarding reminder to user {user_id} for step {current_step}")
                except Exception as user_error:
                    self.logger.error(
                        f"Error processing onboarding reminder for user {user.get('id')}: {str(user_error)}")
        except Exception as e:
            self.logger.error(f"Error sending onboarding reminders: {str(e)}")

    async def send_plan_approval_reminders(self):
        """Отправляет напоминания о необходимости согласования плана питания"""
        try:
            # Проверяем наличие diet_service
            if not self.diet_service:
                self.logger.warning("Diet service is not available for plan approval reminders")
                return

            # Получаем текущее время
            now = DateHelper.get_current_datetime()

            # Получаем планы со статусом pending
            pending_plans = await self.diet_service.get_pending_plans()

            # Создаем стратегию для напоминаний о согласовании плана
            plan_approval_strategy = self._get_reminder_strategy(LK.Reminders.REMINDER_TYPE_PLAN_APPROVAL)
            if not plan_approval_strategy:
                self.logger.warning("Plan approval reminder strategy not found")
                return

            for plan in pending_plans:
                try:
                    user_id = plan.get("user_id")

                    # Получаем пользователя
                    user = await self.user_repository.get_by_id(user_id)
                    if not user or "phone_number" not in user:
                        continue

                    phone_number = user["phone_number"]

                    # Получаем язык пользователя
                    lang = await self.localization_service.get_user_language(user_id)

                    # Проверяем, когда был создан план
                    created_at = datetime.fromisoformat(plan.get("created_at", "2000-01-01T00:00:00"))

                    # Рассчитываем, сколько времени прошло с момента создания
                    hours_passed = (now - created_at).total_seconds() / 3600

                    # Создаем контекст с необходимой информацией
                    context = {
                        "days": int(hours_passed / 24) if hours_passed >= 24 else None
                    }

                    await self._send_reminder(user_id, phone_number, plan_approval_strategy, lang, context)
                except Exception as plan_error:
                    self.logger.error(f"Error processing plan approval reminder: {str(plan_error)}")
        except Exception as e:
            self.logger.error(f"Error sending plan approval reminders: {str(e)}")

    async def send_tracking_reminders(self, context: Dict[str, Any] = None):
        """
        Отправляет напоминания о трекинге с учетом времени суток

        Args:
            context: Контекст выполнения (время суток и т.д.)
        """
        try:
            # Проверяем наличие tracking_service
            if not self.tracking_service:
                self.logger.warning("Tracking service is not available for tracking reminders")
                return

            # Если контекст не передан, создаем его
            if context is None:
                context = self._create_time_context()

            # Получаем пользователей с завершенным онбордингом
            users = await self.user_repository.find_with_completed_onboarding()

            # Получаем все стратегии напоминаний (кроме онбординга и согласования плана)
            reminder_strategies = [
                strategy for strategy in self.reminder_strategies
                if not isinstance(strategy, PlanApprovalReminderStrategy)  # Исключаем напоминания о согласовании плана
            ]

            for user in users:
                try:
                    user_id = user.get("id")
                    phone_number = user.get("phone_number")

                    if not phone_number:
                        continue

                    # Получаем язык пользователя
                    lang = await self.localization_service.get_user_language(user_id)

                    # Получаем данные трекинга на сегодня
                    tracking_status = await self.tracking_service.get_daily_status(user_id)

                    if not tracking_status:
                        continue

                    # Конвертируем объект статуса в словарь для упрощения обработки
                    tracking_data = {
                        "weight_recorded": tracking_status.weight_recorded,
                        "current_water_intake": tracking_status.current_water_intake,
                        "water_goal": tracking_status.water_goal,
                        "water_percentage": tracking_status.water_percentage,
                        "meal_compliance": tracking_status.meal_compliance,
                        "overall_compliance_score": tracking_status.overall_compliance_score
                    }

                    for strategy in reminder_strategies:
                        # Проверяем, нужно ли отправлять напоминание согласно стратегии
                        if await strategy.should_send(user, tracking_data, context):
                            # Отправляем напоминание с использованием вспомогательного метода
                            await self._send_reminder(user_id, phone_number, strategy, lang, context)
                except Exception as user_error:
                    self.logger.error(
                        f"Error processing tracking reminders for user {user.get('id')}: {str(user_error)}"
                    )
        except Exception as e:
            self.logger.error(f"Error sending tracking reminders: {str(e)}")

    async def can_send_reminder(self, phone_number: str, reminder_type: str, min_interval_seconds: int) -> bool:
        """
        Проверяет, можно ли отправить напоминание определенного типа

        Args:
            phone_number: Номер телефона пользователя
            reminder_type: Тип напоминания
            min_interval_seconds: Минимальный интервал между напоминаниями в секундах

        Returns:
            bool: True, если можно отправить напоминание
        """
        try:
            # Получаем последнее напоминание этого типа
            last_reminder = await self.reminder_repository.get_last_reminder(phone_number, reminder_type)

            if not last_reminder:
                return True  # Если напоминаний не было, можно отправить

            # Проверяем, прошло ли минимальное время
            sent_time = datetime.fromisoformat(last_reminder.get("timestamp", ""))
            now = DateHelper.get_current_datetime()

            time_elapsed = (now - sent_time).total_seconds()

            return time_elapsed >= min_interval_seconds
        except Exception as e:
            self.logger.error(f"Error checking if reminder can be sent: {str(e)}")
            return False  # В случае ошибки лучше не отправлять напоминание

    async def record_reminder_sent(self, phone_number: str, reminder_type: str) -> None:
        """
        Записывает информацию об отправленном напоминании

        Args:
            phone_number: Номер телефона пользователя
            reminder_type: Тип напоминания
        """
        try:
            await self.reminder_repository.save_reminder(phone_number, reminder_type)
        except Exception as e:
            self.logger.error(f"Error recording sent reminder: {str(e)}")

    def _get_onboarding_reminder(self, step: str, name: str, lang: str = None) -> str:
        """
        Формирует текст напоминания в зависимости от шага онбординга

        Args:
            step: Шаг онбординга
            name: Имя пользователя
            lang: Код языка

        Returns:
            str: Текст напоминания
        """
        # Базовое обращение с именем, если оно есть
        greeting = self.get_localized_message(LK.Reminders.GREETING, lang)
        if name:
            greeting += ", " + name
        greeting += "! "

        # Выбираем сообщение в зависимости от шага онбординга
        if step == "name":
            return greeting + self.get_localized_message(LK.Reminders.Onboarding.NAME, lang)
        elif step in ["age", "gender", "height"]:
            return greeting + self.get_localized_message(LK.Reminders.Onboarding.BASIC_INFO, lang)
        elif step in ["current_weight", "target_weight"]:
            return greeting + self.get_localized_message(LK.Reminders.Onboarding.WEIGHT_INFO, lang)
        elif step in ["activity_level", "diet_preference", "allergies", "disliked_products", "budget"]:
            return greeting + self.get_localized_message(LK.Reminders.Onboarding.ALMOST_COMPLETE, lang)

        # Общее сообщение по умолчанию
        return greeting + self.get_localized_message(LK.Reminders.Onboarding.DEFAULT, lang)

    def _get_reminder_strategy(self, reminder_type: str) -> Optional[ReminderStrategy]:
        """
        Возвращает стратегию напоминания по типу

        Args:
            reminder_type: Тип напоминания

        Returns:
            Optional[ReminderStrategy]: Стратегия напоминания или None
        """
        for strategy in self.reminder_strategies:
            if strategy.get_reminder_type() == reminder_type:
                return strategy
        return None

    async def _send_reminder(self, user_id: str, phone_number: str, strategy: ReminderStrategy,
                             lang: str = None, context: Dict[str, Any] = None) -> bool:
        """
        Отправляет напоминание с использованием стратегии

        Args:
            user_id: ID пользователя
            phone_number: Номер телефона пользователя
            strategy: Стратегия напоминания
            lang: Код языка
            context: Дополнительный контекст

        Returns:
            bool: Успешность отправки
        """
        try:
            # Получаем константу для типа напоминания
            reminder_type_key = strategy.get_reminder_type()
            reminder_type = self.get_localized_message(reminder_type_key, lang)

            # Проверяем, можно ли отправить напоминание
            if not await self.can_send_reminder(phone_number, reminder_type, strategy.get_interval_seconds()):
                return False

            # Получаем ключ сообщения
            message_key = strategy.get_message_key()

            # Для еженедельного отчета формируем сообщение через сервис трекинга
            if message_key is None and reminder_type == self.get_localized_message(
                    LK.Reminders.REMINDER_TYPE_WEEKLY_REPORT, lang):
                message = await self.tracking_service.generate_weekly_report(user_id)
            else:
                # Передаем дополнительные параметры из контекста
                params = {}
                if context:
                    params.update({k: v for k, v in context.items() if k in ["days"]})

                message = self.get_localized_message(message_key, lang, **params)

            # Отправляем напоминание
            if message:
                reminder_context = {
                    "reminder_type": reminder_type,
                    "user_id": user_id
                }

                # Добавляем дополнительный контекст, если он предоставлен
                if context:
                    reminder_context.update(context)

                # Добавляем тип мессенджера в контекст для корректной отправки
                if "messenger_type" not in reminder_context:
                    # Определяем предпочтительный мессенджер пользователя
                    user = await self.user_repository.get_by_id(user_id)
                    messenger_type = user.get("preferred_messenger", "whatsapp") if user else "whatsapp"
                    reminder_context["messenger_type"] = messenger_type

                await self.messenger_service.send_message(
                    phone_number,
                    message,
                    reminder_context
                )

                # Записываем информацию об отправленном напоминании
                await self.record_reminder_sent(phone_number, reminder_type)

                self.logger.info(f"Sent {reminder_type} reminder to user {user_id}")
                return True

            return False
        except Exception as e:
            self.logger.error(f"Error sending reminder: {str(e)}")
            return False

    def _create_time_context(self, now: datetime = None) -> Dict[str, Any]:
        """
        Создает контекст времени суток для напоминаний

        Args:
            now: Текущее время (если None, используется текущее время системы)

        Returns:
            Dict[str, Any]: Контекст времени суток
        """
        if now is None:
            now = DateHelper.get_current_datetime()

        current_hour = now.hour
        today = now.date()

        return {
            "is_morning": 8 <= current_hour < 12,  # 8:00 - 11:59
            "is_afternoon": 12 <= current_hour < 18,  # 12:00 - 17:59
            "is_evening": 18 <= current_hour < 24,  # 18:00 - 23:59
            "is_night": 24 <= current_hour or current_hour < 8,  # 24:00 - 7:59
            "is_sunday": today.weekday() == 6,  # Воскресенье
            "current_hour": current_hour,
            "today": today.isoformat()
        }

    def log_reminder_status(self) -> Dict[str, Any]:
        """
        Формирует отчет о текущем состоянии сервиса напоминаний для диагностики

        Returns:
            Dict[str, Any]: Статус сервиса напоминаний
        """
        try:
            # Получаем информацию о стратегиях
            strategy_info = []
            for strategy in self.reminder_strategies:
                strategy_info.append({
                    "type": strategy.get_reminder_type(),
                    "message_key": strategy.get_message_key(),
                    "interval_seconds": strategy.get_interval_seconds()
                })

            # Формируем отчет
            return {
                "status": "active",
                "strategies_count": len(self.reminder_strategies),
                "strategies": strategy_info,
                "has_messenger_service": self.messenger_service is not None,
                "has_user_repository": self.user_repository is not None,
                "has_reminder_repository": self.reminder_repository is not None,
                "has_tracking_service": self.tracking_service is not None,
                "has_diet_service": self.diet_service is not None,
                "has_localization_service": self.localization_service is not None
            }
        except Exception as e:
            self.logger.error(f"Error generating reminder status report: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
