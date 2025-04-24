from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Set

import pytz
from pydantic import BaseModel, Field

from config import settings


# Функция для получения текущего времени
def get_current_datetime():
    return datetime.now(pytz.timezone(settings.TIMEZONE))


class ProductCategory(str, Enum):
    FRUITS = "fruits"
    VEGETABLES = "vegetables"
    MEAT = "meat"
    POULTRY = "poultry"
    FISH = "fish"
    DAIRY = "dairy"
    GRAINS = "grains"
    LEGUMES = "legumes"
    NUTS = "nuts"
    OILS = "oils"
    SPICES = "spices"
    SWEETENERS = "sweeteners"
    BEVERAGES = "beverages"
    OTHER = "other"


class NutritionInfo(BaseModel):
    """Информация о пищевой ценности на 100г продукта"""
    calories: float
    proteins: float
    fats: float
    carbs: float
    fiber: Optional[float] = None
    sugar: Optional[float] = None


class ProductStore(BaseModel):
    """Информация о продукте в конкретном магазине"""
    store_name: str  # название магазина
    price: float  # цена в местной валюте
    unit: str  # единица измерения (кг, шт и т.д.)
    available: bool = True

    class Config:
        orm_mode = True


class ProductBase(BaseModel):
    """Базовая модель продукта"""
    name: str
    local_name: Optional[str] = None  # название на местном языке
    category: ProductCategory
    is_local: bool = False  # является ли местным продуктом Гватемалы
    typical_unit: str  # типичная единица измерения

    # Пищевая ценность на 100г
    nutrition: Optional[NutritionInfo] = None

    class Config:
        orm_mode = True


class ProductCreate(ProductBase):
    """Модель для создания продукта"""
    store_data: Optional[List[ProductStore]] = None


class ProductInDB(ProductBase):
    """Модель продукта в базе данных"""
    id: str
    created_at: datetime = Field(default_factory=get_current_datetime)
    updated_at: datetime = Field(default_factory=get_current_datetime)

    # Информация о магазинах
    store_prices: Dict[str, ProductStore] = {}

    # Метаданные
    seasonal: bool = False
    seasonal_months: Optional[List[int]] = None  # список месяцев, когда продукт в сезоне
    regions: Optional[List[str]] = None  # регионы Гватемалы, где распространен продукт
    tags: Optional[Set[str]] = None  # теги для фильтрации (например, "gluten-free", "high-protein")

    class Config:
        orm_mode = True


class ProductResponse(BaseModel):
    """Модель ответа с данными продукта"""
    id: str
    name: str
    local_name: Optional[str] = None
    category: str
    is_local: bool
    typical_unit: str
    nutrition: Optional[NutritionInfo] = None

    # Цены в разных магазинах
    stores: Optional[List[ProductStore]] = None

    class Config:
        orm_mode = True