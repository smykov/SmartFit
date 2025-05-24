import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from datetime import datetime, date, timedelta
import pytz
import json

from app.services.diet.diet_plan_manager import DietPlanManager
from app.models.diet import DietPlan, DietPlanVersion, DietPlanStatus, DailyDiet, Meal, MealType, Product
from app.constants.localization_keys import LocalizationKeys as LK
from app.utils.date_helper import DateHelper


class TestDietPlanManager:

    @pytest.fixture
    def diet_plan_manager(self):
        """Создает экземпляр DietPlanManager с моками зависимостей."""
        llm_service = AsyncMock()
        diet_plan_repository = AsyncMock()
        product_repository = AsyncMock()
        user_repository = AsyncMock()
        localization_service = MagicMock()

        # Настраиваем локализационный сервис для возврата ключей как есть
        localization_service.get_message.side_effect = lambda key, lang=None, **params: key
        localization_service.get_user_language = AsyncMock(return_value="ru")

        # Создаем экземпляр тестируемого класса
        manager = DietPlanManager(
            llm_service=llm_service,
            diet_plan_repository=diet_plan_repository,
            product_repository=product_repository,
            user_repository=user_repository,
            localization_service=localization_service
        )

        # Сохраняем моки в атрибутах для удобного доступа в тестах
        manager.llm_service = llm_service
        manager.diet_plan_repository = diet_plan_repository
        manager.product_repository = product_repository
        manager.user_repository = user_repository
        manager.localization_service = localization_service

        return manager

    @pytest.fixture
    def test_user_data(self):
        """Возвращает тестовые данные пользователя."""
        return {
            "id": "test-user-id",
            "phone_number": "+5012345678",
            "name": "Test User",
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
            "language": "ru"
        }

    @pytest.fixture
    def test_products_data(self):
        """Возвращает тестовые данные о продуктах."""
        return [
            {
                "id": "product-1",
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
                }
            },
            {
                "id": "product-2",
                "name": "Яйца",
                "local_name": "Huevos",
                "category": "dairy",
                "is_local": True,
                "typical_unit": "шт.",
                "nutrition": {
                    "calories": 155,
                    "proteins": 13,
                    "fats": 11,
                    "carbs": 1.1,
                    "fiber": 0
                }
            }
        ]

    @pytest.fixture
    def test_diet_plan_data(self):
        """Возвращает тестовые данные плана диеты."""
        return {
            "id": "test-diet-plan-id",
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

    # Тесты для генерации и создания планов диет

    async def test_generate_short_diet_plan_success(self, diet_plan_manager, test_user_data, test_products_data):
        """Тестирование успешной генерации краткой версии плана диеты."""
        # Arrange
        user_id = "test-user-id"
        short_plan = {
            "daily_plans": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Овсянка с фруктами",
                            "calories": 350
                        }
                    ]
                }
            }
        }

        # Настраиваем моки
        diet_plan_manager.user_repository.get_by_id.return_value = test_user_data
        diet_plan_manager.product_repository.get_all.return_value = test_products_data
        diet_plan_manager.llm_service.generate_completion.return_value = json.dumps(short_plan)
        diet_plan_manager.diet_plan_repository.create.return_value = "new-diet-plan-id"

        # Act
        result = await diet_plan_manager.generate_short_diet_plan(user_id)

        # Assert
        assert result is not None
        assert result["user_id"] == user_id
        assert result["version"] == "short"
        assert result["status"] == "pending"
        assert "daily_plans" in result
        assert "monday" in result["daily_plans"]
        assert result["id"] == "new-diet-plan-id"

        # Verify method calls
        diet_plan_manager.user_repository.get_by_id.assert_called_once_with(user_id)
        diet_plan_manager.product_repository.get_all.assert_called_once()
        diet_plan_manager.llm_service.generate_completion.assert_called_once()
        diet_plan_manager.diet_plan_repository.create.assert_called_once()

    async def test_generate_short_diet_plan_user_not_found(self, diet_plan_manager):
        """Тестирование генерации краткой версии плана диеты, когда пользователь не найден."""
        # Arrange
        user_id = "non-existent-user-id"
        diet_plan_manager.user_repository.get_by_id.return_value = None

        # Act
        result = await diet_plan_manager.generate_short_diet_plan(user_id)

        # Assert
        assert result is None
        diet_plan_manager.user_repository.get_by_id.assert_called_once_with(user_id)
        diet_plan_manager.product_repository.get_all.assert_not_called()
        diet_plan_manager.llm_service.generate_completion.assert_not_called()
        diet_plan_manager.diet_plan_repository.create.assert_not_called()

    async def test_generate_short_diet_plan_llm_error(self, diet_plan_manager, test_user_data, test_products_data):
        """Тестирование генерации краткой версии плана диеты при ошибке LLM-сервиса."""
        # Arrange
        user_id = "test-user-id"

        # Настраиваем моки
        diet_plan_manager.user_repository.get_by_id.return_value = test_user_data
        diet_plan_manager.product_repository.get_all.return_value = test_products_data
        diet_plan_manager.llm_service.generate_completion.side_effect = Exception("LLM service error")

        # Act
        result = await diet_plan_manager.generate_short_diet_plan(user_id)

        # Assert
        assert result is None
        diet_plan_manager.user_repository.get_by_id.assert_called_once_with(user_id)
        diet_plan_manager.product_repository.get_all.assert_called_once()
        diet_plan_manager.llm_service.generate_completion.assert_called_once()
        diet_plan_manager.diet_plan_repository.create.assert_not_called()

    # Тесты для управления статусом плана диеты

    async def test_approve_short_diet_plan_success(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование успешного одобрения краткого плана диеты."""
        # Arrange
        plan_id = "test-diet-plan-id"
        diet_plan_manager.diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_manager.diet_plan_repository.update.return_value = True

        # Act
        result = await diet_plan_manager.approve_short_diet_plan(plan_id)

        # Assert
        assert result is True
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        diet_plan_manager.diet_plan_repository.update.assert_called_once()

        # Check parameters
        update_call_args = diet_plan_manager.diet_plan_repository.update.call_args[0]
        assert update_call_args[0] == plan_id
        assert "status" in update_call_args[1]
        assert update_call_args[1]["status"] == "approved"
        assert "updated_at" in update_call_args[1]

    async def test_approve_short_diet_plan_not_short_version(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование одобрения плана диеты, который не является краткой версией."""
        # Arrange
        plan_id = "test-diet-plan-id"
        full_plan = dict(test_diet_plan_data)
        full_plan["version"] = "full"

        diet_plan_manager.diet_plan_repository.get_by_id.return_value = full_plan

        # Act
        result = await diet_plan_manager.approve_short_diet_plan(plan_id)

        # Assert
        assert result is False
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        diet_plan_manager.diet_plan_repository.update.assert_not_called()

    async def test_approve_short_diet_plan_plan_not_found(self, diet_plan_manager):
        """Тестирование одобрения плана диеты, когда план не найден."""
        # Arrange
        plan_id = "non-existent-plan-id"
        diet_plan_manager.diet_plan_repository.get_by_id.return_value = None

        # Act
        result = await diet_plan_manager.approve_short_diet_plan(plan_id)

        # Assert
        assert result is False
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        diet_plan_manager.diet_plan_repository.update.assert_not_called()

    # Тесты для обновления планов диеты

    async def test_update_short_diet_plan_success(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование успешного обновления краткой версии плана питания."""
        # Arrange
        plan_id = "test-diet-plan-id"
        updated_days = {
            "monday": {
                "meals": [
                    {
                        "type": "breakfast",
                        "title": "Омлет с овощами",
                        "calories": 300
                    },
                    {
                        "type": "lunch",
                        "title": "Куриный салат",
                        "calories": 450
                    }
                ]
            }
        }
        comment = "Заменили овсянку на омлет"

        # Убедимся, что тестовые данные содержат правильную версию
        test_data = test_diet_plan_data.copy()
        test_data["version"] = "short"

        # Настраиваем моки
        diet_plan_manager.diet_plan_repository.get_by_id.return_value = test_data
        diet_plan_manager.diet_plan_repository.update.return_value = True

        # Настраиваем мок для get_user_language
        diet_plan_manager.localization_service.get_user_language = AsyncMock(return_value="ru")

        # Act
        success, updated_plan = await diet_plan_manager.update_short_diet_plan(plan_id, updated_days, comment)

        # Assert
        assert success is True
        assert updated_plan is not None
        assert updated_plan["id"] == plan_id

    async def test_update_short_diet_plan_calculate_total_calories(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование автоматического расчета total_calories при обновлении плана."""
        # Arrange
        plan_id = "test-diet-plan-id"
        updated_days = {
            "monday": {
                "meals": [
                    {
                        "type": "breakfast",
                        "title": "Омлет с овощами",
                        "calories": 300
                    },
                    {
                        "type": "lunch",
                        "title": "Суп",
                        "calories": 250
                    }
                ]
            }
        }

        diet_plan_manager.diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_manager.diet_plan_repository.update.return_value = True

        # Act
        success, updated_plan = await diet_plan_manager.update_short_diet_plan(plan_id, updated_days)

        # Assert
        assert success is True
        assert "monday" in updated_plan["daily_plans"]
        assert "total_calories" in updated_plan["daily_plans"]["monday"]
        assert updated_plan["daily_plans"]["monday"]["total_calories"] == 550  # 300 + 250

    async def test_update_short_diet_plan_plan_not_found(self, diet_plan_manager):
        """Тестирование обновления плана диеты, когда план не найден."""
        # Arrange
        plan_id = "non-existent-plan-id"
        updated_days = {
            "monday": {
                "meals": [
                    {
                        "type": "breakfast",
                        "title": "Омлет с овощами"
                    }
                ]
            }
        }

        diet_plan_manager.diet_plan_repository.get_by_id.return_value = None
        diet_plan_manager.localization_service.get_user_language = AsyncMock(return_value="ru")

        # Act
        success, result = await diet_plan_manager.update_short_diet_plan(plan_id, updated_days)

        # Assert
        assert success is False
        assert "error" in result
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        diet_plan_manager.diet_plan_repository.update.assert_not_called()

    async def test_update_diet_plan_partially_success(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование успешного частичного обновления плана питания."""
        # Arrange
        plan_id = "test-diet-plan-id"
        updated_days = {
            "monday": {
                "meals": [
                    {
                        "type": "breakfast",
                        "title": "Омлет с овощами",
                        "calories": 300
                    },
                    {
                        "type": "lunch",
                        "title": "Суп из чечевицы",
                        "calories": 350
                    }
                ]
            }
        }
        comment = "Обновил завтрак и обед на понедельник"

        diet_plan_manager.diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_manager.diet_plan_repository.update.return_value = True

        # Act
        success, updated_plan = await diet_plan_manager.update_diet_plan_partially(plan_id, updated_days, comment)

        # Assert
        assert success is True
        assert updated_plan is not None
        assert updated_plan["id"] == plan_id

        # Check updated days
        assert "monday" in updated_plan["daily_plans"]
        assert updated_plan["daily_plans"]["monday"]["meals"][0]["title"] == "Омлет с овощами"
        assert updated_plan["daily_plans"]["monday"]["meals"][1]["title"] == "Суп из чечевицы"

        # Check that the other days remained unchanged
        assert "tuesday" in updated_plan["daily_plans"]
        assert updated_plan["daily_plans"]["tuesday"]["meals"][0]["title"] == "Яичница с тостами"

        # Check that total calories were recalculated
        assert updated_plan["daily_plans"]["monday"]["total_calories"] == 650  # 300 + 350

        # Check modification history
        assert "modifications_history" in updated_plan
        assert len(updated_plan["modifications_history"]) == 1
        assert updated_plan["modifications_history"][0]["comment"] == comment

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        diet_plan_manager.diet_plan_repository.update.assert_called_once()

    async def test_update_diet_plan_partially_failure(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование частичного обновления плана, когда обновление в репозитории не удалось."""
        # Arrange
        plan_id = "test-diet-plan-id"
        updated_days = {
            "monday": {
                "meals": [
                    {
                        "type": "breakfast",
                        "title": "Омлет с овощами"
                    }
                ]
            }
        }

        diet_plan_manager.diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_manager.diet_plan_repository.update.return_value = False
        diet_plan_manager.localization_service.get_user_language = AsyncMock(return_value="ru")

        # Act
        success, error = await diet_plan_manager.update_diet_plan_partially(plan_id, updated_days)

        # Assert
        assert success is False
        assert "error" in error
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        diet_plan_manager.diet_plan_repository.update.assert_called_once()

    # Тесты для получения планов диет

    async def test_get_diet_plan_by_id_success(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование успешного получения плана диеты по ID."""
        # Arrange
        plan_id = "test-diet-plan-id"
        diet_plan_manager.diet_plan_repository.get_by_id.return_value = test_diet_plan_data

        # Act
        result = await diet_plan_manager.get_diet_plan_by_id(plan_id)

        # Assert
        assert result is not None
        assert result["id"] == plan_id
        assert result["user_id"] == "test-user-id"
        assert result["version"] == "short"

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)

    async def test_get_diet_plan_by_id_not_found(self, diet_plan_manager):
        """Тестирование получения плана диеты по ID, когда план не найден."""
        # Arrange
        plan_id = "non-existent-plan-id"
        diet_plan_manager.diet_plan_repository.get_by_id.return_value = None

        # Act
        result = await diet_plan_manager.get_diet_plan_by_id(plan_id)

        # Assert
        assert result is None

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)

    async def test_get_current_diet_success(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование успешного получения текущего активного плана диеты пользователя."""
        # Arrange
        user_id = "test-user-id"
        diet_plan_manager.diet_plan_repository.get_current_diet.return_value = test_diet_plan_data

        # Act
        result = await diet_plan_manager.get_current_diet(user_id)

        # Assert
        assert result is not None
        assert result["id"] == "test-diet-plan-id"
        assert result["user_id"] == user_id

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_current_diet.assert_called_once_with(user_id)

    async def test_get_current_diet_not_found(self, diet_plan_manager):
        """Тестирование получения текущего активного плана диеты, когда у пользователя нет планов."""
        # Arrange
        user_id = "test-user-id"
        diet_plan_manager.diet_plan_repository.get_current_diet.return_value = None

        # Act
        result = await diet_plan_manager.get_current_diet(user_id)

        # Assert
        assert result is None

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_current_diet.assert_called_once_with(user_id)

    async def test_get_diet_for_day_success(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование успешного получения плана диеты на конкретный день."""
        # Arrange
        user_id = "test-user-id"
        day_date = date.today()
        weekday = "monday"  # Предполагаем, что сегодня понедельник для упрощения

        # Мокируем метод get_day_of_week для возврата "monday"
        diet_plan_manager.get_day_of_week = MagicMock(return_value=weekday)
        diet_plan_manager.get_current_diet = AsyncMock(return_value=test_diet_plan_data)

        # Act
        result = await diet_plan_manager.get_diet_for_day(user_id, day_date)

        # Assert
        assert result is not None
        assert "meals" in result
        assert len(result["meals"]) == 2
        assert result["meals"][0]["title"] == "Овсянка с фруктами"
        assert result["total_calories"] == 800

        # Verify method calls
        diet_plan_manager.get_current_diet.assert_called_once_with(user_id)
        diet_plan_manager.get_day_of_week.assert_called_once_with(day_date)

    async def test_get_diet_for_day_plan_not_found(self, diet_plan_manager):
        """Тестирование получения плана диеты на день, когда у пользователя нет активного плана."""
        # Arrange
        user_id = "test-user-id"
        day_date = date.today()

        diet_plan_manager.get_current_diet = AsyncMock(return_value=None)
        # Добавляем мок для get_day_of_week, чтобы можно было проверить его вызов
        diet_plan_manager.get_day_of_week = MagicMock()

        # Act
        result = await diet_plan_manager.get_diet_for_day(user_id, day_date)

        # Assert
        assert result is None

        # Verify method calls
        diet_plan_manager.get_current_diet.assert_called_once_with(user_id)
        # Метод get_day_of_week не должен вызываться, если план не найден
        assert not diet_plan_manager.get_day_of_week.called

    async def test_get_diet_for_day_no_plan_for_day(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование получения плана диеты на день, когда для этого дня нет плана."""
        # Arrange
        user_id = "test-user-id"
        day_date = date.today()
        weekday = "sunday"  # День, которого нет в тестовых данных

        # Мокируем метод get_day_of_week для возврата "sunday"
        diet_plan_manager.get_day_of_week = MagicMock(return_value=weekday)
        diet_plan_manager.get_current_diet = AsyncMock(return_value=test_diet_plan_data)

        # Act
        result = await diet_plan_manager.get_diet_for_day(user_id, day_date)

        # Assert
        assert result is None

        # Verify method calls
        diet_plan_manager.get_current_diet.assert_called_once_with(user_id)
        diet_plan_manager.get_day_of_week.assert_called_once_with(day_date)

    async def test_get_today_diet_success(self, diet_plan_manager):
        """Тестирование успешного получения плана диеты на сегодняшний день."""
        # Arrange
        user_id = "test-user-id"
        today_plan = {
            "meals": [
                {
                    "type": "breakfast",
                    "title": "Омлет с овощами"
                }
            ],
            "total_calories": 300
        }

        # Настраиваем мок для метода get_diet_for_day
        diet_plan_manager.get_diet_for_day = AsyncMock(return_value=today_plan)
        DateHelper.get_tracking_date = MagicMock(return_value=datetime.now().date())
        # Act
        result = await diet_plan_manager.get_today_diet(user_id)

        # Assert
        assert result is not None
        assert result == today_plan

        # Verify method calls
        diet_plan_manager.get_diet_for_day.assert_called_once()
        # Проверяем, что метод вызван с правильными параметрами
        args, kwargs = diet_plan_manager.get_diet_for_day.call_args
        assert args[0] == user_id
        assert isinstance(args[1], date)  # Сегодняшняя дата

    async def test_get_diet_for_weekday_success(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование успешного получения плана диеты на конкретный день недели."""
        # Arrange
        user_id = "test-user-id"
        weekday = "monday"

        diet_plan_manager.get_current_diet = AsyncMock(return_value=test_diet_plan_data)

        # Act
        result = await diet_plan_manager.get_diet_for_weekday(user_id, weekday)

        # Assert
        assert result is not None
        assert "meals" in result
        assert len(result["meals"]) == 2
        assert result["meals"][0]["title"] == "Овсянка с фруктами"
        assert result["total_calories"] == 800

        # Verify method calls
        diet_plan_manager.get_current_diet.assert_called_once_with(user_id)

    async def test_get_diet_for_weekday_not_found(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование получения плана диеты на день недели, которого нет в плане."""
        # Arrange
        user_id = "test-user-id"
        weekday = "sunday"  # День, которого нет в тестовых данных

        diet_plan_manager.get_current_diet = AsyncMock(return_value=test_diet_plan_data)

        # Act
        result = await diet_plan_manager.get_diet_for_weekday(user_id, weekday)

        # Assert
        assert result is None

        # Verify method calls
        diet_plan_manager.get_current_diet.assert_called_once_with(user_id)

    # Тесты для обновления плана диеты на основе запроса пользователя

    async def test_update_diet_plan_success(self, diet_plan_manager, test_diet_plan_data, test_user_data):
        """Тестирование успешного обновления плана диеты на основе запроса пользователя."""
        # Arrange
        plan_id = "test-diet-plan-id"
        update_request = "Замени завтрак в понедельник на омлет с овощами"

        # Подготовка ответа от LLM
        llm_response = json.dumps({
            "updated_days": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Омлет с овощами",
                            "calories": 300
                        },
                        {
                            "type": "lunch",
                            "title": "Куриный салат",
                            "calories": 450
                        }
                    ],
                    "total_calories": 750
                }
            },
            "comment": "Заменил овсянку на омлет с овощами согласно вашему запросу"
        })

        diet_plan_manager.diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_manager.llm_service.generate_completion.return_value = llm_response
        # Настраиваем возвращаемые значения
        diet_plan_manager.user_repository.get_by_id = AsyncMock(return_value=test_user_data)
        # Настраиваем метод update_diet_plan_partially
        diet_plan_manager.update_diet_plan_partially = AsyncMock(return_value=(True, test_diet_plan_data))

        # Act
        result = await diet_plan_manager.update_diet_plan(plan_id, update_request)

        # Assert
        assert result["success"] is True
        assert "plan" in result
        assert "comment" in result
        assert "updated_days" in result

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        diet_plan_manager.llm_service.generate_completion.assert_called_once()
        diet_plan_manager.update_diet_plan_partially.assert_called_once()

    async def test_update_diet_plan_parse_error(self, diet_plan_manager, test_diet_plan_data, test_user_data):
        """Тестирование обновления плана диеты, когда невозможно разобрать ответ LLM."""
        # Arrange
        plan_id = "test-diet-plan-id"
        update_request = "Замени завтрак в понедельник на омлет с овощами"

        diet_plan_manager.diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_manager.llm_service.generate_completion.return_value = "Invalid JSON"
        diet_plan_manager.localization_service.get_user_language = AsyncMock(return_value="ru")

        # Настраиваем возвращаемые значения
        diet_plan_manager.user_repository.get_by_id = AsyncMock(return_value=test_user_data)

        # Заменим метод на AsyncMock
        diet_plan_manager.update_diet_plan_partially = AsyncMock()

        # Act
        result = await diet_plan_manager.update_diet_plan(plan_id, update_request)

        # Assert
        assert "error" in result
        assert result["error"] == LK.Diet.Update.PARSING_ERROR

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        diet_plan_manager.llm_service.generate_completion.assert_called_once()

        # Проверка, что метод не вызывался
        diet_plan_manager.update_diet_plan_partially.assert_not_called()

    async def test_update_diet_plan_plan_not_found(self, diet_plan_manager):
        """Тестирование обновления плана диеты, когда план не найден."""
        # Arrange
        plan_id = "non-existent-plan-id"
        update_request = "Замени завтрак в понедельник на омлет с овощами"

        diet_plan_manager.diet_plan_repository.get_by_id.return_value = None
        diet_plan_manager.localization_service.get_user_language = AsyncMock(return_value="ru")
        # Заменим метод на AsyncMock
        diet_plan_manager.update_diet_plan_partially = AsyncMock()
        # Act
        result = await diet_plan_manager.update_diet_plan(plan_id, update_request)

        # Assert
        assert "error" in result
        assert result["error"] == LK.Diet.Full.NO_PLAN

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        # Методы generate_completion и update_diet_plan_partially не должны вызываться
        assert not diet_plan_manager.llm_service.generate_completion.called
        # Проверка, что метод не вызывался
        diet_plan_manager.update_diet_plan_partially.assert_not_called()

    async def test_update_short_diet_plan_by_request_success(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование успешного обновления краткого плана диеты на основе запроса пользователя."""
        # Arrange
        plan_id = "test-diet-plan-id"
        update_request = "Добавь больше белка в завтрак"

        # Подготовка ответа от LLM
        llm_response = json.dumps({
            "updated_days": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Яичница с беконом",
                            "calories": 400
                        },
                        {
                            "type": "lunch",
                            "title": "Куриный салат",
                            "calories": 450
                        }
                    ]
                }
            },
            "comment": "Добавил более белковый завтрак - яичницу с беконом"
        })

        diet_plan_manager.diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_manager.llm_service.generate_completion.return_value = llm_response

        # Настраиваем метод update_short_diet_plan
        updated_plan = dict(test_diet_plan_data)
        updated_plan["daily_plans"]["monday"]["meals"][0]["title"] = "Яичница с беконом"
        diet_plan_manager.update_short_diet_plan = AsyncMock(return_value=(True, updated_plan))

        # Act
        result = await diet_plan_manager.update_short_diet_plan_by_request(plan_id, update_request)

        # Assert
        assert result["success"] is True
        assert "plan" in result
        assert "comment" in result
        assert "updated_days" in result

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        diet_plan_manager.llm_service.generate_completion.assert_called_once()
        diet_plan_manager.update_short_diet_plan.assert_called_once()

    async def test_update_short_diet_plan_by_request_invalid_format(self, diet_plan_manager, test_diet_plan_data):
        """Тестирование обновления краткого плана диеты, когда формат ответа LLM неверен."""
        # Arrange
        plan_id = "test-diet-plan-id"
        update_request = "Добавь больше белка в завтрак"

        # Ответ LLM без ключа updated_days
        llm_response = json.dumps({
            "comment": "Не могу обновить план"
        })

        diet_plan_manager.diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_manager.llm_service.generate_completion.return_value = llm_response
        diet_plan_manager.localization_service.get_user_language = AsyncMock(return_value="ru")

        # Добавляем мок для метода update_short_diet_plan
        diet_plan_manager.update_short_diet_plan = AsyncMock()

        # Act
        result = await diet_plan_manager.update_short_diet_plan_by_request(plan_id, update_request)

        # Assert
        assert "error" in result
        assert result["error"] == LK.Diet.Update.INVALID_FORMAT

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        diet_plan_manager.llm_service.generate_completion.assert_called_once()
        # Теперь можем проверить, что метод не вызывался
        diet_plan_manager.update_short_diet_plan.assert_not_called()

    # Тесты для вспомогательных методов

    def test_get_day_of_week(self, diet_plan_manager):
        """Тестирование метода получения дня недели из даты."""
        # Arrange - Создадим даты для каждого дня недели
        # Monday
        monday = date(2023, 5, 1)  # 1 мая 2023 - понедельник
        tuesday = date(2023, 5, 2)
        wednesday = date(2023, 5, 3)
        thursday = date(2023, 5, 4)
        friday = date(2023, 5, 5)
        saturday = date(2023, 5, 6)
        sunday = date(2023, 5, 7)

        # Act & Assert
        assert diet_plan_manager.get_day_of_week(monday) == "monday"
        assert diet_plan_manager.get_day_of_week(tuesday) == "tuesday"
        assert diet_plan_manager.get_day_of_week(wednesday) == "wednesday"
        assert diet_plan_manager.get_day_of_week(thursday) == "thursday"
        assert diet_plan_manager.get_day_of_week(friday) == "friday"
        assert diet_plan_manager.get_day_of_week(saturday) == "saturday"
        assert diet_plan_manager.get_day_of_week(sunday) == "sunday"

    async def test_get_pending_diet_plan_found(self, diet_plan_manager):
        """Тестирование получения ожидающего подтверждения плана диеты."""
        # Arrange
        user_id = "test-user-id"
        pending_plans = [
            {
                "id": "plan-1",
                "user_id": user_id,
                "version": "short",
                "status": "pending",
                "created_at": "2023-01-01T12:00:00Z"
            },
            {
                "id": "plan-2",
                "user_id": user_id,
                "version": "short",
                "status": "pending",
                "created_at": "2023-01-02T12:00:00Z"  # Более новый план
            }
        ]

        diet_plan_manager.diet_plan_repository.get_user_plans.return_value = pending_plans

        # Act
        result = await diet_plan_manager.get_pending_diet_plan(user_id)

        # Assert
        assert result is not None
        assert result["id"] == "plan-2"  # Должен вернуть самый новый план

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_user_plans.assert_called_once_with(user_id)

    async def test_get_pending_diet_plan_not_found(self, diet_plan_manager):
        """Тестирование получения ожидающего плана, когда таких планов нет."""
        # Arrange
        user_id = "test-user-id"

        # Возвращаем пустой список планов
        diet_plan_manager.diet_plan_repository.get_user_plans.return_value = []

        # Act
        result = await diet_plan_manager.get_pending_diet_plan(user_id)

        # Assert
        assert result is None

        # Verify method calls
        diet_plan_manager.diet_plan_repository.get_user_plans.assert_called_once_with(user_id)