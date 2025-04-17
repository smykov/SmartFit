# app/services/reminders/reminder_factory.py

from typing import Dict, Type, List

from app.services.reminders.reminder_strategies import (
    ReminderStrategy, WeightReminderStrategy, WaterReminderStrategy,
    BreakfastReminderStrategy, LunchReminderStrategy, DinnerReminderStrategy,
    WeeklyReportReminderStrategy, PlanApprovalReminderStrategy
)


class ReminderFactory:
    """Фабрика для создания стратегий напоминаний"""

    @staticmethod
    def create_all_strategies() -> List[ReminderStrategy]:
        """
        Создает все доступные стратегии напоминаний

        Returns:
            List[ReminderStrategy]: Список стратегий
        """
        return [
            WeightReminderStrategy(),
            WaterReminderStrategy(),
            BreakfastReminderStrategy(),
            LunchReminderStrategy(),
            DinnerReminderStrategy(),
            WeeklyReportReminderStrategy(),
            PlanApprovalReminderStrategy()
        ]

    @staticmethod
    def create_strategy(reminder_type: str) -> ReminderStrategy:
        """
        Создает стратегию по типу напоминания

        Args:
            reminder_type: Тип напоминания

        Returns:
            ReminderStrategy: Стратегия напоминания
        """
        strategies = {
            "weight": WeightReminderStrategy(),
            "water": WaterReminderStrategy(),
            "breakfast": BreakfastReminderStrategy(),
            "lunch": LunchReminderStrategy(),
            "dinner": DinnerReminderStrategy(),
            "weekly_report": WeeklyReportReminderStrategy(),
            "plan_approval": PlanApprovalReminderStrategy()
        }

        return strategies.get(reminder_type)