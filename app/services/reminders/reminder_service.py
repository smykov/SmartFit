# app/services/reminders/reminder_service.py

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pytz
import asyncio

from app.db.interfaces.user_repository import IUserRepository
from app.db.interfaces.reminder_repository import IReminderRepository
from app.services.messaging.message_interface import IMessageService
from app.localization.reminder_messages import ReminderMessages
from app.services.tracking.tracking_interface import ITrackingService
from app.services.diet.diet_interface import IDietService
from config import settings


class ReminderService:
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
            message_service: IMessageService,
            user_repository: IUserRepository,
            reminder_repository: IReminderRepository,
            tracking_service: ITrackingService = None,
            diet_service: IDietService = None,
    ):
        """
        Инициализация сервиса напоминаний

        Args:
            message_service: Сервис для отправки сообщений
            user_repository: Репозиторий для работы с пользователями
            reminder_repository: Репозиторий для работы с напоминаниями
            tracking_service: Сервис трекинга (опционально)
            diet_service: Сервис диет (опционально)
        """
        self.message_service = message_service
        self.user_repository = user_repository
        self.reminder_repository = reminder_repository
        self.tracking_service = tracking_service
        self.diet_service = diet_service
        self.messages = ReminderMessages()
        self.logger = logging.getLogger(self.__class__.__name__)

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
                # Текущее время
                now = datetime.now(pytz.timezone(settings.TIMEZONE))
                current_hour = now.hour

                # Пропускаем отправку напоминаний в ночное время
                if 23 <= current_hour or current_hour < 7:
                    await asyncio.sleep(1800)  # 30 минут
                    continue

                # Отправляем напоминания о незавершенном онбординге
                await self.send_onboarding_reminders()

                # Отправляем напоминания о согласовании плана
                await self.send_plan_approval_reminders()

                # Отправляем напоминания о трекинге в зависимости от времени суток
                await self.send_tracking_reminders()

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
            now = datetime.now(pytz.timezone(settings.TIMEZONE))

            # Обрабатываем каждого пользователя
            for user in users:
                try:
                    user_id = user.get("id")
                    phone_number = user.get("phone_number")

                    if not phone_number:
                        continue

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
                        reminder_message = self._get_onboarding_reminder(current_step, user.get("name", ""))

                        # Проверяем, можно ли отправить напоминание
                        if await self.can_send_reminder(phone_number, self.messages.REMINDER_TYPE_ONBOARDING,
                                                        86400):  # 24 часа
                            await self.message_service.send_message(
                                phone_number,
                                reminder_message,
                                current_step
                            )

                            # Записываем информацию об отправленном напоминании
                            await self.record_reminder_sent(phone_number, self.messages.REMINDER_TYPE_ONBOARDING)

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
            now = datetime.now(pytz.timezone(settings.TIMEZONE))

            # Получаем планы со статусом pending
            pending_plans = await self.diet_service.get_pending_plans()

            for plan in pending_plans:
                try:
                    user_id = plan.get("user_id")

                    # Получаем пользователя
                    user = await self.user_repository.get_by_id(user_id)
                    if not user or "phone_number" not in user:
                        continue

                    phone_number = user["phone_number"]

                    # Проверяем, когда был создан план
                    created_at = datetime.fromisoformat(plan.get("created_at", "2000-01-01T00:00:00"))

                    # Рассчитываем, сколько времени прошло с момента создания
                    hours_passed = (now - created_at).total_seconds() / 3600

                    # Проверяем, можно ли отправить напоминание
                    if await self.can_send_reminder(phone_number, self.messages.REMINDER_TYPE_PLAN_APPROVAL,
                                                    14400):  # 4 часа
                        # Выбираем тип напоминания в зависимости от времени ожидания
                        if hours_passed < 4:
                            reminder_message = self.messages.PLAN_APPROVAL_REMINDER_INITIAL
                        elif hours_passed < 24:
                            reminder_message = self.messages.PLAN_APPROVAL_REMINDER_SAME_DAY
                        else:
                            days_passed = int(hours_passed / 24)
                            reminder_message = self.messages.PLAN_APPROVAL_REMINDER_DAYS.format(days=days_passed)

                        # Отправляем напоминание
                        await self.message_service.send_message(
                            phone_number,
                            reminder_message
                        )

                        # Записываем информацию об отправленном напоминании
                        await self.record_reminder_sent(phone_number, self.messages.REMINDER_TYPE_PLAN_APPROVAL)

                        self.logger.info(f"Sent plan approval reminder to user {user_id}")
                except Exception as plan_error:
                    self.logger.error(f"Error processing plan approval reminder: {str(plan_error)}")
        except Exception as e:
            self.logger.error(f"Error sending plan approval reminders: {str(e)}")

    async def send_tracking_reminders(self):
        """Отправляет напоминания о трекинге с учетом времени суток"""
        try:
            # Проверяем наличие tracking_service
            if not self.tracking_service:
                self.logger.warning("Tracking service is not available for tracking reminders")
                return

            # Получаем пользователей с завершенным онбордингом
            users = await self.user_repository.find_with_completed_onboarding()

            # Текущее время и дата
            now = datetime.now(pytz.timezone(settings.TIMEZONE))
            today = now.date()
            current_hour = now.hour

            # Определяем время суток
            is_morning = 5 <= current_hour < 11  # 5:00 - 10:59
            is_afternoon = 11 <= current_hour < 16  # 11:00 - 15:59
            is_evening = 16 <= current_hour < 23  # 16:00 - 22:59

            for user in users:
                try:
                    user_id = user.get("id")
                    phone_number = user.get("phone_number")

                    if not phone_number:
                        continue

                    # Получаем данные трекинга на сегодня
                    tracking_status = await self.tracking_service.get_daily_status(user_id)

                    if not tracking_status:
                        continue

                    # Напоминание о весе по утрам
                    if is_morning and not tracking_status.weight_recorded:
                        if await self.can_send_reminder(phone_number, self.messages.REMINDER_TYPE_WEIGHT,
                                                        86400):  # 24 часа
                            await self.message_service.send_message(
                                phone_number,
                                self.messages.WEIGHT_REMINDER
                            )
                            await self.record_reminder_sent(phone_number, self.messages.REMINDER_TYPE_WEIGHT)

                    # Напоминание о воде
                    if tracking_status.water_percentage < 50:
                        if await self.can_send_reminder(phone_number, self.messages.REMINDER_TYPE_WATER,
                                                        21600):  # 6 часов
                            await self.message_service.send_message(
                                phone_number,
                                self.messages.WATER_REMINDER.format(
                                    percentage=tracking_status.water_percentage
                                )
                            )
                            await self.record_reminder_sent(phone_number, self.messages.REMINDER_TYPE_WATER)

                    # Напоминания о приемах пищи
                    meal_compliance = tracking_status.meal_compliance

                    # Завтрак (утро)
                    if is_morning and "breakfast" not in meal_compliance:
                        if await self.can_send_reminder(phone_number, self.messages.REMINDER_TYPE_BREAKFAST, 86400):
                            await self.message_service.send_message(
                                phone_number,
                                self.messages.BREAKFAST_REMINDER
                            )
                            await self.record_reminder_sent(phone_number, self.messages.REMINDER_TYPE_BREAKFAST)

                    # Обед (день)
                    if is_afternoon and "lunch" not in meal_compliance:
                        if await self.can_send_reminder(phone_number, self.messages.REMINDER_TYPE_LUNCH, 86400):
                            await self.message_service.send_message(
                                phone_number,
                                self.messages.LUNCH_REMINDER
                            )
                            await self.record_reminder_sent(phone_number, self.messages.REMINDER_TYPE_LUNCH)

                    # Ужин (вечер)
                    if is_evening and "dinner" not in meal_compliance:
                        if await self.can_send_reminder(phone_number, self.messages.REMINDER_TYPE_DINNER, 86400):
                            await self.message_service.send_message(
                                phone_number,
                                self.messages.DINNER_REMINDER
                            )
                            await self.record_reminder_sent(phone_number, self.messages.REMINDER_TYPE_DINNER)

                    # Еженедельный отчет по воскресеньям
                    if today.weekday() == 6 and is_evening:  # Воскресенье вечером
                        if await self.can_send_reminder(phone_number, self.messages.REMINDER_TYPE_WEEKLY_REPORT,
                                                        604800):  # 7 дней
                            # Генерируем еженедельный отчет
                            report = await self.tracking_service.generate_weekly_report(user_id)
                            if report:
                                await self.message_service.send_message(phone_number, report)
                                await self.record_reminder_sent(phone_number, self.messages.REMINDER_TYPE_WEEKLY_REPORT)
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
            now = datetime.now(pytz.timezone(settings.TIMEZONE))

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

    def _get_onboarding_reminder(self, step: str, name: str) -> str:
        """
        Формирует текст напоминания в зависимости от шага онбординга

        Args:
            step: Шаг онбординга
            name: Имя пользователя

        Returns:
            str: Текст напоминания
        """
        # Базовое обращение с именем, если оно есть
        greeting = f"{self.messages.BASE_GREETING}{', ' + name if name else ''}! "

        # Выбираем сообщение в зависимости от шага онбординга
        if step == "name":
            return greeting + self.messages.ONBOARDING_REMINDER_NAME
        elif step in ["age", "gender", "height"]:
            return greeting + self.messages.ONBOARDING_REMINDER_BASIC_INFO
        elif step in ["current_weight", "target_weight"]:
            return greeting + self.messages.ONBOARDING_REMINDER_WEIGHT_INFO
        elif step in ["activity_level", "diet_preference", "allergies", "disliked_products", "budget"]:
            return greeting + self.messages.ONBOARDING_REMINDER_ALMOST_COMPLETE

        # Общее сообщение по умолчанию
        return greeting + self.messages.ONBOARDING_REMINDER_DEFAULT