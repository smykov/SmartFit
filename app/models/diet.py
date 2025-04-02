from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, date
import pytz
from enum import Enum

from config import settings

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
    products: List[Product]
    preparation: Optional[str] = None
    calories: Optional[float] = None
    proteins: Optional[float] = None
    fats: Optional[float] = None
    carbs: Optional[float] = None
    
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
    
    # Метаданные
    estimated_total_price: Optional[float] = None
    tips: Optional[str] = None

class DietPlan(BaseModel):
    """Модель плана диеты на неделю"""
    user_id: str
    start_date: date
    end_date: date
    daily_plans: Dict[str, DailyDiet]  # ключ - дата в формате строки
    
    # Метаданные
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone(settings.TIMEZONE)))
    budget_limit: Optional[float] = None
    estimated_weekly_price: Optional[float] = None
    general_recommendations: Optional[str] = None
    
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone(settings.TIMEZONE)))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone(settings.TIMEZONE)))
    total_estimated_price: Optional[float] = None
    
    # Информация о подключении к сервисам доставки
    delivery_integration: Optional[str] = None  # например, "la_torre", "walmart"
    delivery_cart_id: Optional[str] = None
