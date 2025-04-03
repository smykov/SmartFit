from datetime import datetime, date
from enum import Enum
from typing import Optional, Dict

from pydantic import BaseModel

from app.models.diet import MealType


class MealComplianceStatus(str, Enum):
    """Статус соблюдения режима питания"""
    FOLLOWED = "followed"  # Полностью следовал рекомендациям
    PARTIALLY = "partially"  # Частично следовал рекомендациям
    SUBSTITUTED = "substituted"  # Заменил на другое блюдо
    SKIPPED = "skipped"  # Пропустил прием пищи
    NOT_RECORDED = "not_recorded"  # Не записано


class MealCompliance(BaseModel):
    """Запись о соблюдении режима питания"""
    user_id: str
    date: date
    meal_type: MealType
    status: MealComplianceStatus
    notes: Optional[str] = None
    alternative_meal: Optional[str] = None
    created_at: datetime = None

    class Config:
        validate_assignment = True
        extra = "forbid"


class DailyCompliance(BaseModel):
    """Соблюдение режима питания за день"""
    user_id: str
    date: date
    meals: Dict[str, MealComplianceStatus]  # ключ - тип приема пищи
    overall_score: float  # 0-100% соблюдения плана
    notes: Optional[str] = None
    updated_at: datetime = None

    class Config:
        validate_assignment = True
        extra = "forbid"


class WeightEntry(BaseModel):
    """Модель для записи веса"""
    user_id: str
    weight: float  # вес в кг
    date: Optional[date] = None
    notes: Optional[str] = None

    class Config:
        validate_assignment = True
        extra = "forbid"


class WaterIntakeEntry(BaseModel):
    """Модель для записи потребления воды"""
    user_id: str
    amount: float  # количество в мл
    date: Optional[date] = None
    time: Optional[datetime] = None

    class Config:
        validate_assignment = True
        extra = "forbid"


class TrackingData(BaseModel):
    """Модель для сводных данных трекинга"""
    user_id: str
    start_date: date
    end_date: date
    weight_entries: Dict[str, float] = {}  # дата в формате строки: вес
    water_entries: Dict[str, float] = {}  # дата в формате строки: объем воды
    meal_compliance: Dict[str, Dict[str, MealComplianceStatus]] = {}  # дата: {тип приема пищи: статус}

    # Метаданные
    start_weight: Optional[float] = None
    current_weight: Optional[float] = None
    weight_change: Optional[float] = None
    average_water_intake: Optional[float] = None
    average_compliance_score: Optional[float] = None


class DailyTrackingStatus(BaseModel):
    """Статус трекинга на сегодня"""
    user_id: str
    date: date
    weight_recorded: bool = False
    current_water_intake: float = 0  # в мл
    water_goal: float = 2000  # целевое потребление воды в мл
    water_percentage: float = 0  # процент выполнения цели по воде
    meal_compliance: Dict[str, MealComplianceStatus] = {}  # тип приема пищи: статус
    overall_compliance_score: float = 0  # общий процент соблюдения плана

    class Config:
        validate_assignment = True
        extra = "forbid"

    def calculate_water_percentage(self):
        """Рассчитывает процент выполнения цели по воде"""
        if self.water_goal > 0:
            self.water_percentage = min(100, (self.current_water_intake / self.water_goal) * 100)
        return self.water_percentage


class WeightGoalProgress(BaseModel):
    """Прогресс в достижении цели по весу"""
    user_id: str
    start_weight: float
    current_weight: float
    target_weight: float
    total_weight_change: float
    weight_change_percentage: float
    remaining_to_goal: float
    goal_completion_percentage: float

    @classmethod
    def calculate(cls, user_id: str, start_weight: float, current_weight: float, target_weight: float):
        """Рассчитывает прогресс в достижении цели по весу"""
        total_weight_change = current_weight - start_weight

        # Вычисляем оставшийся вес до цели
        remaining_to_goal = current_weight - target_weight

        # Общая цель по изменению веса
        total_goal = start_weight - target_weight

        # Процент изменения от начального веса
        weight_change_percentage = (total_weight_change / start_weight) * 100

        # Процент выполнения цели
        goal_completion_percentage = 0
        if total_goal != 0:
            completed_change = start_weight - current_weight
            goal_completion_percentage = min(100, max(0, (completed_change / abs(total_goal)) * 100))

        return cls(
            user_id=user_id,
            start_weight=start_weight,
            current_weight=current_weight,
            target_weight=target_weight,
            total_weight_change=total_weight_change,
            weight_change_percentage=weight_change_percentage,
            remaining_to_goal=remaining_to_goal,
            goal_completion_percentage=goal_completion_percentage
        )