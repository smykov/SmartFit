import pytest
import uuid
from datetime import datetime, date, timedelta
import pytz
from typing import Dict, Any, List, Optional


@pytest.fixture
def test_user_data():
    """Возвращает тестовые данные пользователя."""
    return {
        "id": f"user-{uuid.uuid4()}",
        "phone_number": "+5012345678",
        "name": "Test User",
        "email": "test@example.com",
        "gender": "male",
        "age": 35,
        "height": 175,
        "current_weight": 85,
        "target_weight": 75,
        "activity_level": "moderate",
        "weight_goal": "lose",
        "diet_preference": "regular",
        "allergies": [],
        "disliked_products": ["mushrooms"],
        "budget_limit": 500,
        "budget_unlimited": False,
        "language": "es",
        "created_at": datetime.now(pytz.UTC).isoformat(),
        "updated_at": datetime.now(pytz.UTC).isoformat(),
        "is_onboarding_completed": True,
        "is_active": True
    }


@pytest.fixture
def test_onboarding_user_data():
    """Возвращает данные пользователя в процессе онбординга."""
    return {
        "id": f"user-{uuid.uuid4()}",
        "phone_number": "+5012345678",
        "name": "New User",
        "onboarding_step": "weight_goal",
        "gender": "female",
        "age": 28,
        "height": 165,
        "current_weight": 70,
        "language": "es",
        "created_at": datetime.now(pytz.UTC).isoformat(),
        "updated_at": datetime.now(pytz.UTC).isoformat(),
        "is_onboarding_completed": False,
        "is_active": True
    }


@pytest.fixture
def test_users_batch(test_user_data):
    """Возвращает набор тестовых пользователей с разными параметрами."""
    base_user = test_user_data.copy()

    users = []

    # Создаем несколько пользователей с разными параметрами
    for i in range(5):
        user = base_user.copy()
        user["id"] = f"user-{uuid.uuid4()}"
        user["phone_number"] = f"+501234567{i}"
        user["name"] = f"Test User {i}"
        user["current_weight"] = 85 - i * 2
        user["target_weight"] = 75 - i * 2
        user["language"] = ["es", "ru", "en"][i % 3]
        users.append(user)

    return users


@pytest.fixture
def inject_test_user(firebase_repositories, test_user_data):
    """Инжектирует тестового пользователя в репозиторий."""

    async def _inject():
        user_repository = firebase_repositories["user_repository"]
        user_id = await user_repository.create(test_user_data)
        return user_id

    return _inject


@pytest.fixture
def inject_onboarding_user(firebase_repositories, test_onboarding_user_data):
    """Инжектирует пользователя в процессе онбординга в репозиторий."""

    async def _inject():
        user_repository = firebase_repositories["user_repository"]
        user_id = await user_repository.create(test_onboarding_user_data)
        return user_id

    return _inject


@pytest.fixture
def inject_users_batch(firebase_repositories, test_users_batch):
    """Инжектирует набор тестовых пользователей в репозиторий."""

    async def _inject():
        user_repository = firebase_repositories["user_repository"]
        user_ids = []
        for user_data in test_users_batch:
            user_id = await user_repository.create(user_data)
            user_ids.append(user_id)
        return user_ids

    return _inject