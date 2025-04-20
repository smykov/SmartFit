import pytest
import uuid
from datetime import datetime, date, timedelta
import pytz
import json
from typing import Dict, Any, List, Optional


@pytest.fixture
def test_diet_plan_data():
    """Возвращает тестовые данные плана диеты."""
    return {
        "id": f"diet-plan-{uuid.uuid4()}",
        "user_id": "test-user-id",
        "version": "short",
        "status": "pending",
        "daily_plans": {
            "monday": {
                "meals": [
                    {
                        "type": "breakfast",
                        "title": "Овсянка с фруктами",
                        "calories": 350,
                        "products": [
                            {"name": "Овсянка", "quantity": 50, "unit": "г"},
                            {"name": "Банан", "quantity": 1, "unit": "шт."}
                        ]
                    },
                    {
                        "type": "lunch",
                        "title": "Куриный салат",
                        "calories": 450,
                        "products": [
                            {"name": "Куриная грудка", "quantity": 150, "unit": "г"},
                            {"name": "Салат", "quantity": 100, "unit": "г"}
                        ]
                    }
                ],
                "total_calories": 800
            },
            "tuesday": {
                "meals": [
                    {
                        "type": "breakfast",
                        "title": "Яичница с тостами",
                        "calories": 400,
                        "products": [
                            {"name": "Яйца", "quantity": 2, "unit": "шт."},
                            {"name": "Хлеб", "quantity": 2, "unit": "ломтика"}
                        ]
                    }
                ],
                "total_calories": 400
            }
        },
        "created_at": datetime.now(pytz.UTC).isoformat(),
        "updated_at": datetime.now(pytz.UTC).isoformat()
    }


@pytest.fixture
def test_shopping_list_data():
    """Возвращает тестовые данные списка покупок."""
    return {
        "id": f"shopping-list-{uuid.uuid4()}",
        "user_id": "test-user-id",
        "diet_plan_id": "test-diet-plan-id",
        "items": [
            {"name": "Овсянка", "quantity": 100, "unit": "г", "category": "bread_cereals", "is_purchased": False},
            {"name": "Яйца", "quantity": 10, "unit": "шт.", "category": "dairy", "is_purchased": False},
            {"name": "Куриная грудка", "quantity": 500, "unit": "г", "category": "meat_fish", "is_purchased": False},
            {"name": "Банан", "quantity": 3, "unit": "шт.", "category": "fruits_vegetables", "is_purchased": False}
        ],
        "created_at": datetime.now(pytz.UTC).isoformat(),
        "updated_at": datetime.now(pytz.UTC).isoformat(),
        "total_estimated_price": 150.0
    }


@pytest.fixture
def test_products_data():
    """Возвращает тестовые данные продуктов."""
    return [
        {
            "id": f"product-{uuid.uuid4()}",
            "name": "Овсянка",
            "local_name": "Avena",
            "category": "grains",
            "is_local": True,
            "typical_unit": "г",
            "nutrition": {
                "calories": 68,
                "proteins": 2.5,
                "fats": 1.8,
                "carbs": 12,
                "fiber": 1.7
            },
            "store_prices": {
                "la_torre": {
                    "store_name": "La Torre",
                    "price": 15.5,
                    "unit": "кг",
                    "available": True
                },
                "walmart": {
                    "store_name": "Walmart",
                    "price": 14.8,
                    "unit": "кг",
                    "available": True
                }
            }
        },
        {
            "id": f"product-{uuid.uuid4()}",
            "name": "Куриная грудка",
            "local_name": "Pechuga de pollo",
            "category": "meat",
            "is_local": True,
            "typical_unit": "г",
            "nutrition": {
                "calories": 165,
                "proteins": 31,
                "fats": 3.6,
                "carbs": 0,
                "fiber": 0
            },
            "store_prices": {
                "la_torre": {
                    "store_name": "La Torre",
                    "price": 55.9,
                    "unit": "кг",
                    "available": True
                },
                "walmart": {
                    "store_name": "Walmart",
                    "price": 52.5,
                    "unit": "кг",
                    "available": True
                }
            }
        }
    ]


@pytest.fixture
def inject_test_diet_plan(firebase_repositories, test_diet_plan_data):
    """Инжектирует тестовый план диеты в репозиторий."""

    async def _inject(user_id=None):
        diet_plan_repository = firebase_repositories["diet_plan_repository"]

        # Если указан ID пользователя, обновляем его в данных плана
        plan_data = test_diet_plan_data.copy()
        if user_id:
            plan_data["user_id"] = user_id

        plan_id = await diet_plan_repository.create(plan_data)
        return plan_id

    return _inject


@pytest.fixture
def inject_test_shopping_list(firebase_repositories, test_shopping_list_data):
    """Инжектирует тестовый список покупок в репозиторий."""

    async def _inject(user_id=None, diet_plan_id=None):
        shopping_list_repository = firebase_repositories["shopping_list_repository"]

        # Если указаны ID пользователя и плана диеты, обновляем их в данных списка покупок
        shopping_list_data = test_shopping_list_data.copy()
        if user_id:
            shopping_list_data["user_id"] = user_id
        if diet_plan_id:
            shopping_list_data["diet_plan_id"] = diet_plan_id

        list_id = await shopping_list_repository.create(shopping_list_data)
        return list_id

    return _inject


@pytest.fixture
def inject_test_products(firebase_repositories, test_products_data):
    """Инжектирует тестовые продукты в репозиторий."""

    async def _inject():
        product_repository = firebase_repositories["product_repository"]

        product_ids = []
        for product_data in test_products_data:
            product_id = await product_repository.create(product_data)
            product_ids.append(product_id)

        return product_ids

    return _inject


@pytest.fixture
def test_weight_entries():
    """Возвращает тестовые записи о весе."""
    today = date.today()
    return [
        {
            "id": f"weight-{uuid.uuid4()}",
            "user_id": "test-user-id",
            "weight": 85.0,
            "date": (today - timedelta(days=7)).isoformat(),
            "notes": "Начальный вес"
        },
        {
            "id": f"weight-{uuid.uuid4()}",
            "user_id": "test-user-id",
            "weight": 84.5,
            "date": (today - timedelta(days=5)).isoformat(),
            "notes": None
        },
        {
            "id": f"weight-{uuid.uuid4()}",
            "user_id": "test-user-id",
            "weight": 84.0,
            "date": (today - timedelta(days=3)).isoformat(),
            "notes": None
        },
        {
            "id": f"weight-{uuid.uuid4()}",
            "user_id": "test-user-id",
            "weight": 83.7,
            "date": today.isoformat(),
            "notes": "Сегодняшний вес"
        }
    ]


@pytest.fixture
def test_water_entries():
    """Возвращает тестовые записи о потреблении воды."""
    today = date.today()
    return [
        {
            "id": f"water-{uuid.uuid4()}",
            "user_id": "test-user-id",
            "amount": 250.0,
            "date": today.isoformat(),
            "time": datetime.now(pytz.UTC).replace(hour=8, minute=0).isoformat()
        },
        {
            "id": f"water-{uuid.uuid4()}",
            "user_id": "test-user-id",
            "amount": 500.0,
            "date": today.isoformat(),
            "time": datetime.now(pytz.UTC).replace(hour=12, minute=0).isoformat()
        },
        {
            "id": f"water-{uuid.uuid4()}",
            "user_id": "test-user-id",
            "amount": 250.0,
            "date": today.isoformat(),
            "time": datetime.now(pytz.UTC).replace(hour=15, minute=0).isoformat()
        }
    ]


@pytest.fixture
def inject_test_weight_entries(firebase_repositories, test_weight_entries):
    """Инжектирует тестовые записи о весе в репозиторий."""

    async def _inject(user_id=None):
        weight_entry_repository = firebase_repositories["weight_entry_repository"]

        entry_ids = []
        for entry_data in test_weight_entries:
            # Если указан ID пользователя, обновляем его в данных записи
            if user_id:
                entry_data = entry_data.copy()
                entry_data["user_id"] = user_id

            entry_id = await weight_entry_repository.add_entry(
                entry_data["user_id"],
                entry_data["weight"],
                date.fromisoformat(entry_data["date"]) if isinstance(entry_data["date"], str) else entry_data["date"],
                entry_data["notes"]
            )
            entry_ids.append(entry_id)

        return entry_ids

    return _inject


@pytest.fixture
def inject_test_water_entries(firebase_repositories, test_water_entries):
    """Инжектирует тестовые записи о потреблении воды в репозиторий."""

    async def _inject(user_id=None):
        water_entry_repository = firebase_repositories["water_entry_repository"]

        entry_ids = []
        for entry_data in test_water_entries:
            # Если указан ID пользователя, обновляем его в данных записи
            if user_id:
                entry_data = entry_data.copy()
                entry_data["user_id"] = user_id

            entry_id = await water_entry_repository.add_entry(
                entry_data["user_id"],
                entry_data["amount"],
                date.fromisoformat(entry_data["date"]) if isinstance(entry_data["date"], str) else entry_data["date"],
                datetime.fromisoformat(entry_data["time"]) if isinstance(entry_data["time"], str) else entry_data[
                    "time"]
            )
            entry_ids.append(entry_id)

        return entry_ids

    return _inject