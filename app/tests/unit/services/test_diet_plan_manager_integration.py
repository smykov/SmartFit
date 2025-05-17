import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from datetime import datetime, date, timedelta
import pytz

from app.services.diet.diet_plan_manager import DietPlanManager
from app.services.diet.diet_service import DietService


class TestDietPlanManagerIntegration:

    @pytest.fixture
    def setup_services(self, firebase_repositories, llm_service_mock, whatsapp_service_mock, localization_service_mock):
        """Настраивает сервисы для интеграционного тестирования."""
        # Создаем моки для репозиториев
        diet_plan_repository = AsyncMock()
        product_repository = AsyncMock()
        user_repository = AsyncMock()
        shopping_list_repository = AsyncMock()

        # Настраиваем базовое поведение моков
        diet_plan_repository.create = AsyncMock()
        diet_plan_repository.get_by_id = AsyncMock()
        diet_plan_repository.update = AsyncMock()
        diet_plan_repository.get_current_diet = AsyncMock()

        product_repository.get_all = AsyncMock(return_value=[])

        user_repository.get_by_id = AsyncMock()
        diet_plan_repository.user_repository = user_repository

        # Создаем DietPlanManager с моками
        diet_plan_manager = DietPlanManager(
            llm_service=llm_service_mock,
            diet_plan_repository=diet_plan_repository,
            product_repository=product_repository,
            user_repository=user_repository,
            localization_service=localization_service_mock
        )

        # Создаем DietService с моками
        diet_service = DietService(
            user_repository=user_repository,
            messenger_service=whatsapp_service_mock,
            localization_service=localization_service_mock,
            diet_plan_repository=diet_plan_repository,
            product_repository=product_repository,
            shopping_list_repository=shopping_list_repository,
            llm_service=llm_service_mock
        )
        diet_service.diet_plan_manager = diet_plan_manager

        return {
            "diet_plan_manager": diet_plan_manager,
            "diet_service": diet_service,
            "user_repository": user_repository,
            "diet_plan_repository": diet_plan_repository,
            "product_repository": product_repository,
            "llm_service": llm_service_mock,
            "whatsapp_service": whatsapp_service_mock,
        }
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
                }
            },
            "created_at": datetime.now(pytz.UTC).isoformat(),
            "updated_at": datetime.now(pytz.UTC).isoformat()
        }

    async def test_generate_and_approve_diet_plan(self, setup_services, test_user_data):
        """Тестирование полного потока генерации и одобрения плана диеты."""
        # Arrange
        user_id = "test-user-id"
        diet_plan_manager = setup_services["diet_plan_manager"]
        diet_service = setup_services["diet_service"]

        # Создаем моки для всех зависимостей
        mock_user_repo = AsyncMock()
        mock_diet_plan_repo = AsyncMock()
        mock_product_repo = AsyncMock()
        mock_llm_service = AsyncMock()

        # Настраиваем возвращаемые значения
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user_data)

        short_plan_response = {
            "daily_plans": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Овсянка с фруктами",
                            "calories": 350
                        },
                        {
                            "type": "lunch",
                            "title": "Куриный салат",
                            "calories": 450
                        }
                    ],
                    "total_calories": 800
                }
            }
        }

        mock_llm_service.generate_completion = AsyncMock(return_value=json.dumps(short_plan_response))
        mock_product_repo.get_all = AsyncMock(return_value=[])
        mock_diet_plan_repo.create = AsyncMock(return_value="new-diet-plan-id")
        mock_diet_plan_repo.get_by_id = AsyncMock(
            return_value={
                "id": "new-diet-plan-id",
                "user_id": user_id,
                "version": "short",
                "status": "pending",
                "daily_plans": short_plan_response["daily_plans"],
                "created_at": datetime.now(pytz.UTC).isoformat(),
                "updated_at": datetime.now(pytz.UTC).isoformat()
            }
        )
        mock_diet_plan_repo.update = AsyncMock(return_value=True)

        # Заменяем зависимости на наши моки
        diet_plan_manager.user_repository = mock_user_repo
        diet_plan_manager.diet_plan_repository = mock_diet_plan_repo
        diet_plan_manager.product_repository = mock_product_repo
        diet_plan_manager.llm_service = mock_llm_service

        # Act - Генерация краткого плана
        short_plan = await diet_service.generate_short_diet_plan(user_id)

        # Assert - Проверка краткого плана
        assert short_plan is not None
        assert short_plan["id"] == "new-diet-plan-id"
        assert short_plan["user_id"] == user_id
        assert short_plan["version"] == "short"
        assert short_plan["status"] == "pending"

        # Act - Одобрение плана
        approval_result = await diet_service.approve_short_diet_plan("new-diet-plan-id")

        # Assert - Проверка результата одобрения
        assert approval_result is True
        mock_diet_plan_repo.update.assert_called_once()
        # Проверка, что статус был изменен на "approved"
        assert mock_diet_plan_repo.update.call_args[0][1]["status"] == "approved"

    async def test_update_diet_flow(self, setup_services, test_diet_plan_data, test_user_data):
        """Тестирование полного потока обновления плана диеты."""
        # Arrange
        plan_id = "test-diet-plan-id"
        update_request = "Замени завтрак в понедельник на омлет с овощами"

        diet_plan_manager = setup_services["diet_plan_manager"]
        diet_service = setup_services["diet_service"]
        diet_plan_repository = setup_services["diet_plan_repository"]
        llm_service = setup_services["llm_service"]

        # Настройка мока репозитория планов диет
        diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_repository.update.return_value = True

        # Настраиваем возвращаемые значения
        diet_plan_manager.user_repository.get_by_id = AsyncMock(return_value=test_user_data)

        # Создаем правильный ответ LLM
        llm_response = {
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
        }

        # Заменяем side_effect для generate_completion
        async def mock_generate_completion(*args, **kwargs):
            return json.dumps(llm_response)

        llm_service.generate_completion.side_effect = mock_generate_completion

        # Мокируем localization_service.get_user_language для корректной работы
        diet_plan_manager.localization_service.get_user_language = AsyncMock(return_value="ru")

        # Создаем обновленный план для возврата из update_diet_plan_partially
        updated_plan = test_diet_plan_data.copy()
        updated_plan["daily_plans"]["monday"]["meals"][0]["title"] = "Омлет с овощами"
        diet_plan_manager.update_diet_plan_partially = AsyncMock(return_value=(True, updated_plan))

        # Act
        result = await diet_service.update_diet_plan(plan_id, update_request)

        # Assert
        assert "error" not in result
        assert result["success"] is True
        assert "plan" in result
        assert "comment" in result
        assert "updated_days" in result

        # Проверяем вызовы методов
        diet_plan_repository.get_by_id.assert_called_once_with(plan_id)
        llm_service.generate_completion.assert_called_once()
        diet_plan_manager.update_diet_plan_partially.assert_called_once()

    async def test_get_diet_for_specific_day(self, setup_services, test_diet_plan_data):
        """Тестирование получения плана диеты на конкретный день через DietService."""
        # Arrange
        user_id = "test-user-id"
        diet_service = setup_services["diet_service"]
        diet_plan_repository = setup_services["diet_plan_repository"]

        # Добавляем информацию для вторника
        test_diet_plan_data["daily_plans"]["tuesday"] = {
            "meals": [
                {
                    "type": "breakfast",
                    "title": "Яичница с тостами",
                    "calories": 400
                },
                {
                    "type": "lunch",
                    "title": "Овощной суп",
                    "calories": 250
                }
            ],
            "total_calories": 650
        }

        # Настраиваем мок репозитория плана диеты
        diet_plan_repository.get_current_diet.return_value = test_diet_plan_data

        # Создаем дату для вторника (предположим, что это завтра)
        today = date.today()
        tuesday_date = today + timedelta(days=1)

        # Мокируем get_day_of_week для возврата "tuesday"
        with patch.object(diet_service.diet_plan_manager, 'get_day_of_week', return_value="tuesday"):
            # Act
            result = await diet_service.get_diet_for_day(user_id, tuesday_date)

        # Assert
        assert result is not None
        assert "meals" in result
        assert len(result["meals"]) == 2
        assert result["meals"][0]["title"] == "Яичница с тостами"
        assert result["total_calories"] == 650

        # Проверяем, что вызывались нужные методы
        diet_plan_repository.get_current_diet.assert_called_once_with(user_id)