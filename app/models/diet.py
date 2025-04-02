from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, date
import pytz
from enum import Enum

from config import settings


# Функция для получения текущего времени с учетом временной зоны
def get_current_datetime():
    return datetime.now(pytz.timezone(settings.TIMEZONE))


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class Product(BaseModel):
    """Модель продукта"""
    name: str
    quantity: float
    unit: str  # граммы, мл, штуки и т.д.
    calories: Optional[float] = None  # на порцию
    price: Optional[float] = None  # в местной валюте


class Meal(BaseModel):
    """Модель приема пищи"""
    type: MealType
    title: str
    description: Optional[str] = None
    why_recommended: Optional[str] = None  # Пояснение, почему блюдо рекомендовано
    relevance_score: Optional[int] = None  # Показатель соответствия целям (1-10)

    products: List[Product]
    preparation: Optional[str] = None
    calories: Optional[float] = None
    proteins: Optional[float] = None
    fats: Optional[float] = None
    carbs: Optional[float] = None
    fiber: Optional[float] = None
    vitamins: Optional[str] = None
    minerals: Optional[str] = None

    # Технические метаданные
    local_products_percentage: Optional[float] = None
    estimated_price: Optional[float] = None


class DailyDiet(BaseModel):
    """Модель диеты на один день"""
    date: date
    meals: List[Meal]
    total_calories: Optional[float] = None
    total_proteins: Optional[float] = None
    total_fats: Optional[float] = None
    total_carbs: Optional[float] = None
    macros_ratio: Optional[str] = None

    # Метаданные
    estimated_total_price: Optional[float] = None
    tips: Optional[str] = None

class DietPlanVersion(str, Enum):
    SHORT = "short"  # Краткая версия для согласования
    FULL = "full"    # Полная версия с рецептами

class DietPlanStatus(str, Enum):
    PENDING = "pending"    # Ожидает согласования
    APPROVED = "approved"  # Согласован, ждет полной версии
    IN_PROGRESS = "in_progress" # В процессе генерации полного плана
    ACTIVE = "active"      # Активный план (полная версия)
    ARCHIVED = "archived"  # Архивный план

class WeekDay(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class DietPlan(BaseModel):
    """Модель плана диеты на неделю по дням недели"""
    user_id: str
    version: DietPlanVersion = DietPlanVersion.SHORT
    status: DietPlanStatus = DietPlanStatus.PENDING
    daily_plans: Dict[str, DailyDiet]  # ключ - дата в формате строки

    # Метаданные
    created_at: datetime = Field(default_factory=get_current_datetime)
    updated_at: datetime = Field(default_factory=get_current_datetime)
    budget_limit: Optional[float] = None
    estimated_weekly_price: Optional[float] = None
    general_recommendations: Optional[str] = None
    personalized_note: Optional[str] = None  # Персональное обращение к пользователю
    caloric_deficit: Optional[str] = None  # Рассчитанный дефицит калорий
    caloric_proficit: Optional[str] = None  # Рассчитанный профицит калорий

    # Технические данные
    ai_generated: bool = True
    dietitian_approved: bool = False
    dietitian_comments: Optional[str] = None


class ShoppingListItem(BaseModel):
    """Элемент списка покупок"""
    name: str
    quantity: float
    unit: str
    estimated_price: Optional[float] = None
    store_suggestions: Optional[List[str]] = None
    is_purchased: bool = False


class ShoppingList(BaseModel):
    """Список покупок на основе плана диеты"""
    user_id: str
    diet_plan_id: str
    items: List[ShoppingListItem]

    # Метаданные
    created_at: datetime = Field(default_factory=get_current_datetime)
    updated_at: datetime = Field(default_factory=get_current_datetime)
    total_estimated_price: Optional[float] = None

    # Информация о подключении к сервисам доставки
    delivery_integration: Optional[str] = None  # например, "la_torre", "walmart"
    delivery_cart_id: Optional[str] = None