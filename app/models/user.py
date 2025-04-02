from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import pytz
from enum import Enum

from config import settings

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"  # Сидячий образ жизни
    LIGHT = "light"  # Легкая активность (1-3 раза в неделю)
    MODERATE = "moderate"  # Умеренная активность (3-5 раз в неделю)
    HIGH = "high"  # Высокая активность (6-7 раз в неделю)
    VERY_HIGH = "very_high"  # Очень высокая активность (профессиональный спорт)

class WeightGoal(str, Enum):
    LOSE = "lose"  # Похудение
    MAINTAIN = "maintain"  # Поддержание веса
    GAIN = "gain"  # Набор массы

class DietPreference(str, Enum):
    REGULAR = "regular"  # Обычная диета
    VEGETARIAN = "vegetarian"  # Вегетарианская
    VEGAN = "vegan"  # Веганская
    LOW_CARB = "low_carb"  # Низкоуглеводная
    KETO = "keto"  # Кето-диета
    GLUTEN_FREE = "gluten_free"  # Безглютеновая

class UserBase(BaseModel):
    """Базовая модель пользователя"""
    phone_number: str
    name: str
    email: Optional[EmailStr] = None
    
    # Профиль для диеты
    gender: Optional[Gender] = None
    age: Optional[int] = None
    height: Optional[float] = None  # в см
    current_weight: Optional[float] = None  # в кг
    target_weight: Optional[float] = None  # в кг
    activity_level: Optional[ActivityLevel] = None
    weight_goal: Optional[WeightGoal] = None
    diet_preference: Optional[DietPreference] = None
    
    # Дополнительные данные
    budget_limit: Optional[float] = None  # бюджет на еду в местной валюте
    allergies: Optional[List[str]] = []
    disliked_products: Optional[List[str]] = []
    local_cuisine_preference: Optional[bool] = True
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 18 or v > 100):
            raise ValueError('Возраст должен быть в диапазоне от 18 до 100 лет')
        return v
    
    @validator('height')
    def validate_height(cls, v):
        if v is not None and (v < 100 or v > 250):
            raise ValueError('Рост должен быть в диапазоне от 100 до 250 см')
        return v
    
    @validator('current_weight', 'target_weight')
    def validate_weight(cls, v):
        if v is not None and (v < 30 or v > 300):
            raise ValueError('Вес должен быть в диапазоне от 30 до 300 кг')
        return v

class UserCreate(UserBase):
    """Модель для создания пользователя"""
    pass

class UserUpdate(BaseModel):
    """Модель для обновления пользователя"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    gender: Optional[Gender] = None
    age: Optional[int] = None
    height: Optional[float] = None
    current_weight: Optional[float] = None
    target_weight: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    weight_goal: Optional[WeightGoal] = None
    diet_preference: Optional[DietPreference] = None
    budget_limit: Optional[float] = None
    allergies: Optional[List[str]] = None
    disliked_products: Optional[List[str]] = None
    local_cuisine_preference: Optional[bool] = None

class UserInDB(UserBase):
    """Модель пользователя в базе данных"""
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone(settings.TIMEZONE)))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone(settings.TIMEZONE)))
    
    # Флаги состояния
    is_onboarding_completed: bool = False
    is_active: bool = True
    
    # Информация для трекинга
    weight_history: Dict[str, float] = {}  # дата: вес
    water_intake_history: Dict[str, float] = {}  # дата: объем воды в мл
    
    # Метаданные
    last_interaction: Optional[datetime] = None
    registration_source: str = "whatsapp"
    
    class Config:
        orm_mode = True

class UserResponse(BaseModel):
    """Модель ответа с данными пользователя"""
    id: str
    phone_number: str
    name: str
    email: Optional[EmailStr] = None
    is_onboarding_completed: bool
    
    # Базовая информация для диеты
    gender: Optional[Gender] = None
    age: Optional[int] = None
    current_weight: Optional[float] = None
    target_weight: Optional[float] = None
    weight_goal: Optional[WeightGoal] = None
    
    class Config:
        orm_mode = True
