# app/services/reminders/reminder_strategies.py

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any

from app.constants.localization_keys import LocalizationKeys as LK


class ReminderStrategy(ABC):
    """Базовый класс стратегии для напоминаний"""

    @abstractmethod
    async def should_send(self, user: Dict[str, Any], tracking_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Определяет, нужно ли отправлять напоминание

        Args:
            user: Данные пользователя
            tracking_data: Данные трекинга
            context: Контекст (время суток и т.д.)

        Returns:
            bool: True, если нужно отправить напоминание
        """
        pass

    @abstractmethod
    def get_reminder_type(self) -> str:
        """
        Возвращает тип напоминания

        Returns:
            str: Тип напоминания
        """
        pass

    @abstractmethod
    def get_message_key(self) -> str:
        """
        Возвращает ключ сообщения

        Returns:
            str: Ключ сообщения напоминания
        """
        pass

    @abstractmethod
    def get_interval_seconds(self) -> int:
        """
        Возвращает минимальный интервал между напоминаниями в секундах

        Returns:
            int: Интервал в секундах
        """
        pass


class WeightReminderStrategy(ReminderStrategy):
    """Стратегия для напоминаний о весе"""

    async def should_send(self, user: Dict[str, Any], tracking_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Отправляем напоминание утром и если вес еще не записан
        return context.get("is_morning", False) and not tracking_data.get("weight_recorded", False)

    def get_reminder_type(self) -> str:
        return LK.Reminders.REMINDER_TYPE_WEIGHT

    def get_message_key(self) -> str:
        return LK.Reminders.WEIGHT_REMINDER

    def get_interval_seconds(self) -> int:
        return 86400  # 24 часа


class WaterReminderStrategy(ReminderStrategy):
    """Стратегия для напоминаний о потреблении воды"""

    async def should_send(self, user: Dict[str, Any], tracking_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Отправляем напоминание, если процент потребления воды низкий (менее 50%)
        water_percentage = tracking_data.get("water_percentage", 0)

        # Не отправляем ночью, независимо от процента
        if context.get("is_night", False):
            return False

        # Если потребление воды меньше 50% от целевого, отправляем напоминание
        return water_percentage < 50

    def get_reminder_type(self) -> str:
        return LK.Reminders.REMINDER_TYPE_WATER

    def get_message_key(self) -> str:
        return LK.Reminders.WATER_REMINDER

    def get_interval_seconds(self) -> int:
        return 21600  # 6 часов


class BreakfastReminderStrategy(ReminderStrategy):
    """Стратегия для напоминаний о завтраке"""

    async def should_send(self, user: Dict[str, Any], tracking_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Отправляем напоминание утром, если завтрак еще не отмечен
        is_morning = context.get("is_morning", False)
        meal_compliance = tracking_data.get("meal_compliance", {})

        # Проверяем, что о завтраке еще нет записи
        breakfast_tracked = "breakfast" in meal_compliance

        return is_morning and not breakfast_tracked

    def get_reminder_type(self) -> str:
        return LK.Reminders.REMINDER_TYPE_BREAKFAST

    def get_message_key(self) -> str:
        return LK.Reminders.BREAKFAST_REMINDER

    def get_interval_seconds(self) -> int:
        return 86400  # 24 часа (напоминаем раз в день)


class LunchReminderStrategy(ReminderStrategy):
    """Стратегия для напоминаний об обеде"""

    async def should_send(self, user: Dict[str, Any], tracking_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Отправляем напоминание днем, если обед еще не отмечен
        is_afternoon = context.get("is_afternoon", False)
        meal_compliance = tracking_data.get("meal_compliance", {})

        # Проверяем, что об обеде еще нет записи
        lunch_tracked = "lunch" in meal_compliance

        return is_afternoon and not lunch_tracked

    def get_reminder_type(self) -> str:
        return LK.Reminders.REMINDER_TYPE_LUNCH

    def get_message_key(self) -> str:
        return LK.Reminders.LUNCH_REMINDER

    def get_interval_seconds(self) -> int:
        return 86400  # 24 часа (напоминаем раз в день)


class DinnerReminderStrategy(ReminderStrategy):
    """Стратегия для напоминаний об ужине"""

    async def should_send(self, user: Dict[str, Any], tracking_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Отправляем напоминание вечером, если ужин еще не отмечен
        is_evening = context.get("is_evening", False)
        meal_compliance = tracking_data.get("meal_compliance", {})

        # Проверяем, что об ужине еще нет записи
        dinner_tracked = "dinner" in meal_compliance

        return is_evening and not dinner_tracked

    def get_reminder_type(self) -> str:
        return LK.Reminders.REMINDER_TYPE_DINNER

    def get_message_key(self) -> str:
        return LK.Reminders.DINNER_REMINDER

    def get_interval_seconds(self) -> int:
        return 86400  # 24 часа (напоминаем раз в день)


class WeeklyReportReminderStrategy(ReminderStrategy):
    """Стратегия для еженедельных отчетов"""

    async def should_send(self, user: Dict[str, Any], tracking_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Отправляем отчет по воскресеньям вечером
        is_sunday = context.get("is_sunday", False)
        is_evening = context.get("is_evening", False)

        return is_sunday and is_evening

    def get_reminder_type(self) -> str:
        return LK.Reminders.REMINDER_TYPE_WEEKLY_REPORT

    def get_message_key(self) -> str:
        # Для этого типа напоминаний сообщение формируется динамически сервисом трекинга
        return None

    def get_interval_seconds(self) -> int:
        return 604800  # 7 дней (напоминаем раз в неделю)


class PlanApprovalReminderStrategy(ReminderStrategy):
    """Стратегия для напоминаний о согласовании плана питания"""

    async def should_send(self, user: Dict[str, Any], tracking_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Напоминаем о согласовании, если есть ожидающий план
        has_pending_plan = context.get("has_pending_plan", False)

        # Не отправляем ночью, независимо от наличия плана
        if context.get("is_night", False):
            return False

        return has_pending_plan

    def get_reminder_type(self) -> str:
        return LK.Reminders.REMINDER_TYPE_PLAN_APPROVAL

    def get_message_key(self) -> str:
        # Ключ сообщения зависит от времени, прошедшего с создания плана
        # Установим дефолтное значение, а конкретный ключ будет выбран в сервисе
        return LK.Reminders.PLAN_APPROVAL_REMINDER_INITIAL

    def get_interval_seconds(self) -> int:
        return 14400  # 4 часа (можем напоминать несколько раз в день)