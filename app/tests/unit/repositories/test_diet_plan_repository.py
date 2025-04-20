# tests/unit/repositories/test_diet_plan_repository.py
import pytest

from app.db.repositories.diet_plan_repository import FirebaseDietPlanRepository

class TestDietPlanRepository:

    @pytest.fixture
    def diet_plan_repository(self, firebase_mock):
        """Создание тестового экземпляра репозитория плана диеты."""
        return FirebaseDietPlanRepository(firebase_mock)

    async def test_create_diet_plan(self, diet_plan_repository, firebase_mock):
        """Тест создания нового плана диеты."""
        # Настраиваем мок Firebase
        firebase_mock.add_document.return_value = "new-diet-plan-id"

        # Тестовые данные
        diet_plan_data = {
            "user_id": "test-user-id",
            "version": "short",
            "status": "pending",
            "daily_plans": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Овсянка с фруктами"
                        }
                    ]
                }
            }
        }

        # Вызываем тестируемый метод
        result = await diet_plan_repository.create(diet_plan_data)

        # Проверяем результат
        assert result == "new-diet-plan-id"

        # Проверяем, что метод add_document был вызван с правильными аргументами
        firebase_mock.add_document.assert_called_once()

        # Проверка дополнительных полей в аргументах (modified)
        args, kwargs = firebase_mock.add_document.call_args
        assert args[0] == "diet_plans"  # Проверяем имя коллекции
        assert "created_at" in args[1]
        assert "updated_at" in args[1]

    async def test_update_diet_plan(self, diet_plan_repository, firebase_mock):
        """Тест обновления существующего плана диеты."""
        # Настраиваем мок Firebase
        firebase_mock.update_document.return_value = True

        # Тестовые данные для обновления
        plan_id = "test-diet-plan-id"
        update_data = {
            "daily_plans": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Омлет с овощами"
                        }
                    ]
                }
            }
        }

        # Вызываем тестируемый метод
        result = await diet_plan_repository.update(plan_id, update_data)

        # Проверяем результат
        assert result is True

        # Проверяем, что вызов метода происходит с правильными параметрами
        firebase_mock.update_document.assert_called_once()
        args, kwargs = firebase_mock.update_document.call_args
        assert args[0] == "diet_plans"
        assert args[1] == plan_id
        assert "daily_plans" in args[2]
        assert "updated_at" in args[2]

    async def test_get_current_diet(self, diet_plan_repository, firebase_mock):
        """Тест получения текущего активного плана диеты пользователя."""
        # Настраиваем мок Firebase
        user_id = "test-user-id"
        active_plan = {
            "id": "active-plan-id",
            "user_id": user_id,
            "version": "full",
            "status": "active",
            "created_at": "2023-01-02T12:00:00Z",
            "daily_plans": {}
        }

        # Важно: устанавливаем return_value, а не используем return_value на корутине
        firebase_mock.query_documents.return_value = [active_plan]

        # Вызываем тестируемый метод
        result = await diet_plan_repository.get_current_diet(user_id)

        # Проверяем результат
        assert result is not None
        assert result["id"] == "active-plan-id"
        assert result["status"] == "active"

        # Проверяем, что firebase_mock.query_documents был вызван с правильными параметрами
        firebase_mock.query_documents.assert_called_once_with(
            "diet_plans", "user_id", "==", user_id
        )

    async def test_update_daily_plan(self, diet_plan_repository, firebase_mock):
        """Тест обновления плана на конкретный день."""
        # Настраиваем моки
        test_plan = {
            "id": "test-diet-plan-id",
            "user_id": "test-user-id",
            "daily_plans": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Овсянка"
                        }
                    ]
                }
            }
        }

        firebase_mock.get_document.return_value = test_plan
        firebase_mock.update_document.return_value = True

        # Тестовые данные
        plan_id = "test-diet-plan-id"
        day_key = "monday"
        day_data = {
            "meals": [
                {
                    "type": "breakfast",
                    "title": "Омлет с овощами"
                }
            ]
        }

        # Вызываем тестируемый метод
        result = await diet_plan_repository.update_daily_plan(plan_id, day_key, day_data)

        # Проверяем результат
        assert result is True

        # Проверяем, что методы были вызваны с правильными параметрами
        firebase_mock.get_document.assert_called_once_with("diet_plans", plan_id)
        firebase_mock.update_document.assert_called_once()
