# tests/unit/services/test_diet_service.py
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock, ANY
from datetime import datetime, date, timedelta
import pytz

from app.services.diet.diet_service import DietService
from app.models.diet import DietPlan, DietPlanVersion, DietPlanStatus, DailyDiet, Meal, MealType, Product


class TestDietService:

    @pytest.fixture
    def diet_service_dependencies(self):
        """Фикстура для создания моков зависимостей DietService."""
        dependencies = {
            "user_repository": AsyncMock(),
            "messenger_service": AsyncMock(),
            "localization_service": MagicMock(),
            "diet_plan_repository": AsyncMock(),
            "product_repository": AsyncMock(),
            "shopping_list_repository": AsyncMock(),
            "llm_service": AsyncMock()
        }

        # Настройка возвращаемых значений для часто используемых методов
        dependencies["localization_service"].get_message.return_value = "Локализованное сообщение"
        dependencies["localization_service"].get_user_language = AsyncMock(return_value="ru")

        return dependencies

    @pytest.fixture
    def diet_service(self, diet_service_dependencies):
        """Фикстура для создания тестируемого экземпляра DietService."""
        service = DietService(**diet_service_dependencies)

        # Заменяем моками менеджеры и форматтеры
        service.diet_plan_manager = AsyncMock()
        service.shopping_list_manager = AsyncMock()
        service.formatter = MagicMock()

        return service

    @pytest.fixture
    def test_user_data(self):
        """Фикстура для создания тестовых данных пользователя."""
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
        """Фикстура для создания тестовых данных плана диеты."""
        return {
            "id": "test-diet-plan-id",
            "user_id": "test-user-id",
            "version": "short",
            "status": "pending",
            "daily_plans": {
                "monday": {
                    "date": date.today().isoformat(),
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
                    "date": (date.today() + timedelta(days=1)).isoformat(),
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
    def test_shopping_list_data(self):
        """Фикстура для создания тестовых данных списка покупок."""
        return {
            "id": "test-shopping-list-id",
            "user_id": "test-user-id",
            "diet_plan_id": "test-diet-plan-id",
            "items": [
                {"name": "Овсянка", "quantity": 100, "unit": "г", "category": "bread_cereals", "is_purchased": False},
                {"name": "Яйца", "quantity": 10, "unit": "шт.", "category": "dairy", "is_purchased": False},
                {"name": "Куриная грудка", "quantity": 500, "unit": "г", "category": "meat_fish",
                 "is_purchased": False},
                {"name": "Банан", "quantity": 3, "unit": "шт.", "category": "fruits_vegetables", "is_purchased": False}
            ],
            "total_estimated_price": 150.0
        }

    #
    # 1. Тесты для методов генерации диеты
    #

    async def test_generate_short_diet_plan_success(self, diet_service, diet_service_dependencies, test_user_data,
                                                    test_diet_plan_data):
        """Тестирование успешной генерации краткой версии плана диеты."""
        # Arrange
        user_id = "test-user-id"
        diet_service.diet_plan_manager.generate_short_diet_plan.return_value = test_diet_plan_data

        # Act
        result = await diet_service.generate_short_diet_plan(user_id)

        # Assert
        assert result is not None
        assert result["id"] == "test-diet-plan-id"
        assert result["user_id"] == user_id
        assert result["version"] == "short"
        assert result["status"] == "pending"
        assert "daily_plans" in result
        assert "monday" in result["daily_plans"]

        # Verify calls
        diet_service.diet_plan_manager.generate_short_diet_plan.assert_called_once_with(user_id)

    async def test_generate_full_diet_plan_success(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование успешной генерации полной версии плана диеты."""
        # Arrange
        short_plan_id = "test-diet-plan-id"
        test_full_diet_plan_data = dict(test_diet_plan_data)
        test_full_diet_plan_data["version"] = "full"
        test_full_diet_plan_data["status"] = "active"

        # Настраиваем diet_plan_manager.get_diet_plan_by_id
        diet_service.diet_plan_manager.get_diet_plan_by_id.return_value = test_diet_plan_data

        # Настраиваем user_repository.get_by_id
        diet_service_dependencies["user_repository"].get_by_id.return_value = {"id": "test-user-id"}

        # Создаем мок для класса ProgressiveDietGenerator
        mock_generator_instance = AsyncMock()
        mock_generator_instance.generate_full_plan.return_value = test_full_diet_plan_data

        # Создаем мок для конструктора класса
        mock_generator_class = MagicMock(return_value=mock_generator_instance)

        # Патчим сам модуль
        with patch.dict('sys.modules', {
            'app.services.progressive_diet_generator': MagicMock(
                ProgressiveDietGenerator=mock_generator_class
            )
        }):
            # Act
            result = await diet_service.generate_full_diet_plan(short_plan_id)

            # Assert
            assert result is not None
            assert result["id"] == "test-diet-plan-id"
            assert result["version"] == "full"
            assert result["status"] == "active"

            # Verify calls
            diet_service.diet_plan_manager.get_diet_plan_by_id.assert_called_once_with(short_plan_id)
            diet_service_dependencies["user_repository"].get_by_id.assert_called_once()
            mock_generator_class.assert_called_once()
            mock_generator_instance.generate_full_plan.assert_called_once()

    async def test_start_full_diet_generation_success(self, diet_service, diet_service_dependencies,
                                                      test_diet_plan_data):
        """Тестирование запуска фоновой генерации полной версии плана диеты."""
        # Arrange
        user_id = "test-user-id"
        short_plan_id = "test-diet-plan-id"
        diet_service_dependencies["user_repository"].get_by_id.return_value = {"phone_number": "+1234567890"}

        # Мокируем asyncio.create_task, чтобы не запускать реальную фоновую задачу
        with patch('asyncio.create_task') as mock_create_task:
            # Act
            result = await diet_service.start_full_diet_generation(user_id, short_plan_id)

            # Assert
            assert result is True

            # Verify calls
            mock_create_task.assert_called_once()

    #
    # 2. Тесты для методов обновления диеты
    #

    async def test_update_diet_plan_success(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование успешного обновления плана диеты."""
        # Arrange
        plan_id = "test-diet-plan-id"
        update_request = "Замени завтрак в понедельник на омлет с овощами"

        expected_result = {
            "success": True,
            "plan": dict(test_diet_plan_data),
            "comment": "Завтрак в понедельник заменен на омлет с овощами",
            "updated_days": {"monday": {"meals": [{"type": "breakfast", "title": "Омлет с овощами"}]}}
        }

        diet_service.diet_plan_manager.update_diet_plan.return_value = expected_result

        # Act
        result = await diet_service.update_diet_plan(plan_id, update_request)

        # Assert
        assert result is not None
        assert result["success"] is True
        assert "plan" in result
        assert "comment" in result
        assert "updated_days" in result

        # Verify calls
        diet_service.diet_plan_manager.update_diet_plan.assert_called_once_with(plan_id, update_request)

    async def test_update_short_diet_plan_by_request_success(self, diet_service, diet_service_dependencies,
                                                             test_diet_plan_data):
        """Тестирование успешного обновления краткого плана диеты на основе запроса пользователя."""
        # Arrange
        plan_id = "test-diet-plan-id"
        update_request = "Замени обед на вторник на суп из чечевицы"

        expected_result = {
            "success": True,
            "plan": dict(test_diet_plan_data),
            "comment": "Обед во вторник заменен на суп из чечевицы",
            "updated_days": {"tuesday": {"meals": [{"type": "lunch", "title": "Суп из чечевицы"}]}}
        }

        diet_service.diet_plan_manager.update_short_diet_plan_by_request.return_value = expected_result

        # Act
        result = await diet_service.update_short_diet_plan_by_request(plan_id, update_request)

        # Assert
        assert result is not None
        assert result["success"] is True
        assert "plan" in result
        assert "comment" in result
        assert "updated_days" in result

        # Verify calls
        diet_service.diet_plan_manager.update_short_diet_plan_by_request.assert_called_once_with(plan_id,
                                                                                                 update_request)

    async def test_approve_short_diet_plan_success(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование успешного одобрения краткого плана диеты."""
        # Arrange
        plan_id = "test-diet-plan-id"
        diet_service.diet_plan_manager.approve_short_diet_plan.return_value = True

        # Act
        result = await diet_service.approve_short_diet_plan(plan_id)

        # Assert
        assert result is True

        # Verify calls
        diet_service.diet_plan_manager.approve_short_diet_plan.assert_called_once_with(plan_id)

    #
    # 3. Тесты для методов получения диеты
    #

    async def test_get_current_diet_success(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование успешного получения текущего плана диеты."""
        # Arrange
        user_id = "test-user-id"
        diet_service.diet_plan_manager.get_current_diet.return_value = test_diet_plan_data

        # Act
        result = await diet_service.get_current_diet(user_id)

        # Assert
        assert result is not None
        assert result["id"] == "test-diet-plan-id"
        assert result["user_id"] == user_id

        # Verify calls
        diet_service.diet_plan_manager.get_current_diet.assert_called_once_with(user_id)

    async def test_get_current_diet_not_found(self, diet_service, diet_service_dependencies):
        """Тестирование сценария, когда текущий план диеты не найден."""
        # Arrange
        user_id = "test-user-id"
        diet_service.diet_plan_manager.get_current_diet.return_value = None

        # Act
        result = await diet_service.get_current_diet(user_id)

        # Assert
        assert result is None

        # Verify calls
        diet_service.diet_plan_manager.get_current_diet.assert_called_once_with(user_id)

    async def test_get_diet_for_day_success(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование успешного получения плана диеты на конкретный день."""
        # Arrange
        user_id = "test-user-id"
        day_date = date.today()
        day_data = test_diet_plan_data["daily_plans"]["monday"]
        diet_service.diet_plan_manager.get_diet_for_day.return_value = day_data

        # Act
        result = await diet_service.get_diet_for_day(user_id, day_date)

        # Assert
        assert result is not None
        assert "meals" in result

        # Verify calls
        diet_service.diet_plan_manager.get_diet_for_day.assert_called_once_with(user_id, day_date)

    async def test_get_diet_for_day_not_found(self, diet_service, diet_service_dependencies):
        """Тестирование сценария, когда план на запрашиваемый день не найден."""
        # Arrange
        user_id = "test-user-id"
        day_date = date.today() + timedelta(days=7)
        diet_service.diet_plan_manager.get_diet_for_day.return_value = None

        # Act
        result = await diet_service.get_diet_for_day(user_id, day_date)

        # Assert
        assert result is None

        # Verify calls
        diet_service.diet_plan_manager.get_diet_for_day.assert_called_once_with(user_id, day_date)

    async def test_get_pending_diet_plan_success(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование успешного получения ожидающего одобрения плана диеты."""
        # Arrange
        user_id = "test-user-id"
        diet_service.diet_plan_manager.get_pending_diet_plan.return_value = test_diet_plan_data

        # Act
        result = await diet_service.get_pending_diet_plan(user_id)

        # Assert
        assert result is not None
        assert result["id"] == "test-diet-plan-id"
        assert result["status"] == "pending"

        # Verify calls
        diet_service.diet_plan_manager.get_pending_diet_plan.assert_called_once_with(user_id)

    async def test_get_pending_diet_plan_not_found(self, diet_service, diet_service_dependencies):
        """Тестирование сценария, когда ожидающий план не найден."""
        # Arrange
        user_id = "test-user-id"
        diet_service.diet_plan_manager.get_pending_diet_plan.return_value = None

        # Act
        result = await diet_service.get_pending_diet_plan(user_id)

        # Assert
        assert result is None

        # Verify calls
        diet_service.diet_plan_manager.get_pending_diet_plan.assert_called_once_with(user_id)

    async def test_get_pending_plans(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование получения всех ожидающих одобрения планов диеты."""
        # Arrange
        pending_plans = [test_diet_plan_data]
        diet_service_dependencies["diet_plan_repository"].find_by_status.return_value = pending_plans

        # Act
        result = await diet_service.get_pending_plans()

        # Assert
        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == "test-diet-plan-id"

        # Verify calls
        diet_service_dependencies["diet_plan_repository"].find_by_status.assert_called_once_with("pending")

    #
    # 4. Тесты для методов форматирования
    #

    def test_get_diet_summary(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование получения сводки плана диеты."""
        # Arrange
        lang = "ru"
        diet_service.formatter.get_diet_summary.return_value = "Сводка плана диеты"

        # Act
        result = diet_service.get_diet_summary(test_diet_plan_data, lang)

        # Assert
        assert result == "Сводка плана диеты"

        # Verify calls
        diet_service.formatter.get_diet_summary.assert_called_once_with(test_diet_plan_data, lang)

    def test_get_diet_summary_commands(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование получения команд для плана диеты."""
        # Arrange
        lang = "ru"
        diet_service.formatter.get_diet_summary_commands.return_value = "Команды для плана диеты"

        # Act
        result = diet_service.get_diet_summary_commands(test_diet_plan_data, lang)

        # Assert
        assert result == "Команды для плана диеты"

        # Verify calls
        diet_service.formatter.get_diet_summary_commands.assert_called_once_with(test_diet_plan_data, lang)

    def test_get_full_diet_plan(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование получения полного плана диеты на все дни."""
        # Arrange
        lang = "ru"
        diet_service.formatter.get_full_diet_plan.return_value = ["День 1", "День 2"]

        # Act
        result = diet_service.get_full_diet_plan(test_diet_plan_data, lang)

        # Assert
        assert result == ["День 1", "День 2"]

        # Verify calls
        diet_service.formatter.get_full_diet_plan.assert_called_once_with(test_diet_plan_data, lang)

    def test_get_day_diet_plan(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование получения плана диеты на конкретный день."""
        # Arrange
        day_date = date.today()
        lang = "ru"
        diet_service.formatter.get_day_diet_plan.return_value = ["Завтрак", "Обед"]

        # Act
        result = diet_service.get_day_diet_plan(test_diet_plan_data, day_date, lang)

        # Assert
        assert result == ["Завтрак", "Обед"]

        # Verify calls
        diet_service.formatter.get_day_diet_plan.assert_called_once_with(test_diet_plan_data, day_date, lang)

    def test_get_short_diet_summary(self, diet_service, diet_service_dependencies, test_diet_plan_data):
        """Тестирование получения сводки краткой версии плана диеты."""
        # Arrange
        lang = "ru"
        diet_service.formatter.get_short_diet_summary.return_value = "Сводка краткого плана диеты"

        # Act
        result = diet_service.get_short_diet_summary(test_diet_plan_data, lang)

        # Assert
        assert result == "Сводка краткого плана диеты"

        # Verify calls
        diet_service.formatter.get_short_diet_summary.assert_called_once_with(test_diet_plan_data, lang)

    def test_get_short_diet_next_steps(self, diet_service, diet_service_dependencies):
        """Тестирование получения информации о следующих шагах после создания краткого плана."""
        # Arrange
        lang = "ru"
        diet_service.formatter.get_short_diet_next_steps.return_value = "Следующие шаги"

        # Act
        result = diet_service.get_short_diet_next_steps(lang)

        # Assert
        assert result == "Следующие шаги"

        # Verify calls
        diet_service.formatter.get_short_diet_next_steps.assert_called_once_with(lang)

    def test_get_diet_tracking_info_message(self, diet_service, diet_service_dependencies):
        """Тестирование получения информации о трекинге диеты."""
        # Arrange
        lang = "ru"
        diet_service.formatter.get_diet_tracking_info_message.return_value = "Информация о трекинге"

        # Act
        result = diet_service.get_diet_tracking_info_message(lang)

        # Assert
        assert result == "Информация о трекинге"

        # Verify calls
        diet_service.formatter.get_diet_tracking_info_message.assert_called_once_with(lang)

    #
    # 5. Тесты для методов работы со списком покупок
    #

    async def test_generate_shopping_list_success(self, diet_service, diet_service_dependencies, test_diet_plan_data,
                                                  test_shopping_list_data):
        """Тестирование успешной генерации списка покупок."""
        # Arrange
        diet_plan_id = "test-diet-plan-id"
        lang = "ru"
        diet_service_dependencies["diet_plan_repository"].get_by_id.return_value = test_diet_plan_data
        diet_service.shopping_list_manager.generate_shopping_list.return_value = test_shopping_list_data

        # Act
        result = await diet_service.generate_shopping_list(diet_plan_id, lang)

        # Assert
        assert result is not None
        assert result["id"] == "test-shopping-list-id"
        assert result["diet_plan_id"] == "test-diet-plan-id"
        assert "items" in result
        assert len(result["items"]) > 0

        # Verify calls
        diet_service_dependencies["diet_plan_repository"].get_by_id.assert_called_once_with(diet_plan_id)
        diet_service.shopping_list_manager.generate_shopping_list.assert_called_once_with(diet_plan_id, lang)

    async def test_generate_shopping_list_diet_plan_not_found(self, diet_service, diet_service_dependencies):
        """Тестирование генерации списка покупок, когда план диеты не найден."""
        # Arrange
        lang = "ru"
        diet_plan_id = "non-existent-plan-id"
        diet_service_dependencies["diet_plan_repository"].get_by_id.return_value = None

        # Настраиваем оригинальный метод shopping_list_manager.generate_shopping_list
        # для возврата объекта с ошибкой, если он будет вызван
        original_method = diet_service.shopping_list_manager.generate_shopping_list
        diet_service.shopping_list_manager.generate_shopping_list = AsyncMock(return_value={
            "error": "Diet plan not found"
        })

        try:
            # Act
            result = await diet_service.generate_shopping_list(diet_plan_id, lang)

            # Assert
            assert result is not None
            assert result.get("success") is False
            assert "message" in result

            # Verify calls
            diet_service_dependencies["diet_plan_repository"].get_by_id.assert_called_once_with(diet_plan_id)
            diet_service.shopping_list_manager.generate_shopping_list.assert_called_once_with(diet_plan_id, lang)
        finally:
            # Восстанавливаем оригинальный метод
            diet_service.shopping_list_manager.generate_shopping_list = original_method

    async def test_mark_product_as_purchased_success(self, diet_service, diet_service_dependencies, test_diet_plan_data,
                                                     test_shopping_list_data):
        """Тестирование успешной отметки продукта как купленного."""
        # Arrange
        user_id = "test-user-id"
        product_name = "Овсянка"
        diet_service.shopping_list_manager.mark_product_as_purchased.return_value = {
            "success": True,
            "message": "Продукт отмечен как купленный"
        }

        # Act
        result = await diet_service.mark_product_as_purchased(user_id, product_name)

        # Assert
        assert result["success"] is True
        assert "message" in result

        # Verify calls
        diet_service.shopping_list_manager.mark_product_as_purchased.assert_called_once_with(user_id, product_name)

    async def test_mark_product_as_purchased_product_not_found(self, diet_service, diet_service_dependencies):
        """Тестирование отметки продукта как купленного, когда продукт не найден."""
        # Arrange
        user_id = "test-user-id"
        product_name = "Несуществующий продукт"
        diet_service.shopping_list_manager.mark_product_as_purchased.return_value = {
            "success": False,
            "message": "Продукт не найден"
        }

        # Act
        result = await diet_service.mark_product_as_purchased(user_id, product_name)

        # Assert
        assert result["success"] is False
        assert "message" in result

        # Verify calls
        diet_service.shopping_list_manager.mark_product_as_purchased.assert_called_once_with(user_id, product_name)

    def test_format_shopping_list(self, diet_service, diet_service_dependencies, test_shopping_list_data):
        """Тестирование форматирования списка покупок."""
        # Arrange
        lang = "ru"
        diet_service.formatter.format_shopping_list.return_value = "Отформатированный список покупок"

        # Act
        result = diet_service.format_shopping_list(test_shopping_list_data, lang)

        # Assert
        assert result == "Отформатированный список покупок"

        # Verify calls
        diet_service.formatter.format_shopping_list.assert_called_once_with(test_shopping_list_data, lang)

    #
    # 6. Тесты для других методов
    #

    async def test_answer_nutrition_question_success(self, diet_service, diet_service_dependencies, test_user_data):
        """Тестирование успешного ответа на вопрос о питании."""
        # Arrange
        lang = "ru"
        user_id = "test-user-id"
        question = "Можно ли есть авокадо при похудении?"

        diet_service_dependencies["user_repository"].get_by_id.return_value = test_user_data
        diet_service_dependencies[
            "llm_service"].answer_nutrition_question.return_value = "Да, авокадо можно есть при похудении..."

        # Act
        result = await diet_service.answer_nutrition_question(user_id, question, lang)

        # Assert
        assert result is not None
        assert "Да, авокадо можно" in result

        # Verify calls
        diet_service_dependencies["user_repository"].get_by_id.assert_called_once_with(user_id)
        diet_service_dependencies["llm_service"].answer_nutrition_question.assert_called_once_with(user_id, question)

    async def test_answer_nutrition_question_user_not_found(self, diet_service, diet_service_dependencies):
        """Тестирование ответа на вопрос о питании, когда пользователь не найден."""
        # Arrange
        lang = "ru"
        user_id = "non-existent-user-id"
        question = "Можно ли есть авокадо при похудении?"

        diet_service_dependencies["user_repository"].get_by_id.return_value = None

        # Act
        result = await diet_service.answer_nutrition_question(user_id, question, lang)

        # Assert
        assert result is not None

        # Verify calls
        diet_service_dependencies["user_repository"].get_by_id.assert_called_once_with(user_id)
        diet_service_dependencies["llm_service"].answer_nutrition_question.assert_not_called()
